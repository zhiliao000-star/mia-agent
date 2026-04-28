from typing import Any

import pytest
from langchain_core.messages import AIMessage

from mia.graphs import memory_court
from mia.settings import Settings


class SequentialCourtLlm:
    def __init__(self, responses: list[str]):
        self.responses = responses

    async def ainvoke(self, _messages: list[Any]) -> AIMessage:
        if not self.responses:
            raise AssertionError("No fake LLM responses left")
        return AIMessage(content=self.responses.pop(0))


def settings() -> Settings:
    return Settings(
        OPENAI_API_KEY="key",
        OPENAI_BASE_URL="https://llm.test/v1",
        MODEL_NAME="model",
    )


@pytest.mark.asyncio
async def test_memory_court_runs_two_adversarial_rounds_then_judges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        '[{"memory_ids":["mem1"],"action":"delete","proposed_content":null,"reason":"low value"}]',
        '[{"proposal_index":0,"argument":"Could still matter later","should_keep":true}]',
        '[{"proposal_index":0,"argument":"No durable signal","should_keep":false}]',
        '[{"memory_ids":["mem1"],"action":"delete","final_content":null,"reason":"decay wins"}]',
    ]
    fake = SequentialCourtLlm(responses)
    monkeypatch.setattr(memory_court, "build_chat_model", lambda *_args, **_kwargs: fake)

    graph = memory_court.build_memory_court_graph(settings())
    result = await graph.ainvoke(
        {
            "run_id": "court-1",
            "local_date": "2026-04-27",
            "memories": [
                {
                    "id": "mem1",
                    "content": "temporary note",
                    "tier": "short_term",
                    "segment": "facts",
                    "importanceScore": 0.1,
                    "decayRate": 0.3,
                    "status": "active",
                }
            ],
            "proposals": [],
            "adversarial_rounds": [],
            "judge_decisions": [],
            "round": 0,
        }
    )

    assert result["round"] == 2
    assert len(result["adversarial_rounds"]) == 2
    assert result["judge_decisions"][0]["action"] == "delete"
    assert responses == []
