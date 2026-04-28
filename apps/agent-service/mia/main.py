import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from mia.graphs.memory_court import build_memory_court_graph
from mia.graphs.router import build_router_graph
from mia.integrations.convex import ConvexClient
from mia.integrations.sendblue import SendBlueClient
from mia.models import SendBlueWebhook
from mia.settings import Settings, get_settings
from mia.tools.computer import execute_pending_action

app = FastAPI(title="Mia Agent Service", version="0.1.0")


def get_convex(settings: Settings = Depends(get_settings)) -> ConvexClient:
    return ConvexClient(settings)


def get_sendblue(settings: Settings = Depends(get_settings)) -> SendBlueClient:
    return SendBlueClient(settings)


@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    llm_status = "configured" if all(
        [settings.openai_api_key, settings.openai_base_url, settings.model_name]
    ) else "missing"
    return {"status": "ok", "llm": llm_status}


@app.post("/webhooks/sendblue/receive")
async def receive_sendblue(
    payload: SendBlueWebhook,
    sb_signing_secret: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    convex: ConvexClient = Depends(get_convex),
    sendblue: SendBlueClient = Depends(get_sendblue),
) -> dict[str, object]:
    if settings.sendblue_webhook_secret and sb_signing_secret != settings.sendblue_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    if payload.is_outbound:
        await convex.record_webhook_event(payload, ignored=True)
        return {"ok": True, "ignored": "outbound"}

    accepted = await convex.record_inbound_message(payload)
    if not accepted:
        return {"ok": True, "deduped": True}

    from_number = payload.from_number or payload.number
    if payload.content.strip().lower() == "approve":
        if not settings.owner_phone_number or from_number != settings.owner_phone_number:
            reply = "I can only accept approvals from the owner number."
        else:
            action = await convex.approve_pending_action(requester_number=from_number)
            if not action:
                reply = "No pending action to approve."
            elif action.get("error") == "multiple":
                reply = "There is more than one pending action. Ask me to retry after clearing older requests."
            elif action.get("error"):
                reply = "No pending action to approve."
            else:
                try:
                    result = execute_pending_action(action)
                    await convex.complete_pending_action(
                        code=action["code"],
                        requester_number=from_number,
                        result=result,
                    )
                    reply = f"Approved and completed:\n{result[:1200]}"
                except Exception as exc:
                    await convex.fail_pending_action(
                        code=action["code"],
                        requester_number=from_number,
                        error=str(exc),
                    )
                    reply = f"Approved, but execution failed: {exc}"
        outbound = await sendblue.send_message(number=from_number, content=reply)
        await convex.record_outbound_message(payload, reply, outbound)
        return {"ok": True, "reply": reply, "route": "approval"}

    run_id = str(uuid.uuid4())
    await convex.start_agent_run(run_id=run_id, message_handle=payload.message_handle)
    relevant_memories = await convex.relevant_memories(message=payload.content)
    graph = build_router_graph(settings, convex)
    try:
        result = await graph.ainvoke(
            {
                "run_id": run_id,
                "message": payload.content,
                "relevant_memories": relevant_memories,
                "from_number": payload.from_number or payload.number,
                "sendblue_number": payload.sendblue_number or payload.to_number,
                "message_handle": payload.message_handle,
                "route": "direct_reply",
                "sub_agent_name": "",
                "sub_agent_objective": "",
                "allowed_tools": [],
                "agent_result": "",
                "reply": "",
                "thoughts": [],
            }
        )
    except Exception as exc:
        await convex.fail_agent_run(run_id=run_id, error=str(exc))
        raise

    reply = result["reply"]
    try:
        outbound = await sendblue.send_message(number=payload.from_number or payload.number, content=reply)
        await convex.record_outbound_message(payload, reply, outbound)
        await convex.complete_agent_run(run_id=run_id, active_agent=result["route"])
    except Exception as exc:
        await convex.log_thought(
            message_handle=payload.message_handle,
            run_id=run_id,
            node="sendblue_outbound",
            content=f"Failed to send outbound iMessage: {exc}",
            active_agent=None,
        )
        await convex.fail_agent_run(run_id=run_id, error=str(exc))
        raise
    return {"ok": True, "reply": reply, "route": result["route"]}


@app.post("/internal/memory-court/run")
async def run_memory_court(
    request: Request,
    x_mia_internal_secret: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    convex: ConvexClient = Depends(get_convex),
) -> dict[str, object]:
    if not settings.mia_internal_secret or x_mia_internal_secret != settings.mia_internal_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")

    body = await request.json()
    run_id = body.get("runId")
    local_date = body.get("localDate")
    if not isinstance(run_id, str) or not run_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing runId")
    if not isinstance(local_date, str) or not local_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing localDate")
    memories = await convex.list_court_candidate_memories()
    graph = build_memory_court_graph(settings)
    result = await graph.ainvoke(
        {
            "run_id": run_id,
            "local_date": local_date,
            "memories": memories,
            "proposals": [],
            "adversarial_rounds": [],
            "judge_decisions": [],
            "round": 0,
        }
    )
    await convex.apply_memory_court_decisions(run_id=run_id, result=result)
    return {"ok": True, "runId": run_id, "decisions": len(result["judge_decisions"])}
