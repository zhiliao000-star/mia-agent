from langchain_core.tools import StructuredTool

from mia.integrations.convex import ConvexClient


def build_calendar_tools(convex: ConvexClient, *, source_message_handle: str) -> list[StructuredTool]:
    async def list_calendar_events(day: str) -> str:
        normalized = day.strip() or "today"
        holds = await convex.list_calendar_holds(day=normalized)
        if not holds:
            return f"No Mia calendar holds found for {normalized}."
        rendered = "; ".join(
            f"{hold['time']} {hold['title']} ({hold['status']})" for hold in holds
        )
        return f"Mia calendar holds for {normalized}: {rendered}."

    async def create_calendar_hold(title: str, day: str, time: str) -> str:
        hold_id = await convex.create_calendar_hold(
            title=title.strip(),
            day=day.strip(),
            time=time.strip(),
            source_message_handle=source_message_handle,
        )
        return f"Tentative calendar hold created: {title} on {day} at {time}. Hold ID: {hold_id}."

    return [
        StructuredTool.from_function(
            coroutine=list_calendar_events,
            name="list_calendar_events",
            description="List Mia calendar holds for a requested day.",
        ),
        StructuredTool.from_function(
            coroutine=create_calendar_hold,
            name="create_calendar_hold",
            description="Create a tentative Mia calendar hold with title, day, and time.",
        ),
    ]
