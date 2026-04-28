from langchain_core.tools import BaseTool

from mia.integrations.convex import ConvexClient
from mia.tools.calendar import build_calendar_tools
from mia.tools.coding import CODING_TOOLS
from mia.tools.computer import build_computer_tools
from mia.tools.search import build_search_tools


AVAILABLE_TOOL_NAMES = {
    "list_calendar_events",
    "create_calendar_hold",
    "explain_code_request",
    "propose_test_cases",
    "open_url",
    "open_app",
    "read_file",
    "write_file",
    "delete_file",
    "run_terminal_command",
    "web_search",
}


def tool_registry(
    convex: ConvexClient,
    *,
    source_message_handle: str,
    requester_number: str = "",
    run_id: str | None = None,
    searxng_base_url: str = "",
) -> dict[str, BaseTool]:
    tools: list[BaseTool] = [
        *build_calendar_tools(convex, source_message_handle=source_message_handle),
        *CODING_TOOLS,
        *build_computer_tools(
            convex,
            requester_number=requester_number,
            message_handle=source_message_handle,
            run_id=run_id,
        ),
        *build_search_tools(searxng_base_url=searxng_base_url),
    ]
    return {tool.name: tool for tool in tools}


def public_tool_descriptions() -> str:
    return "\n".join(
        [
            "- list_calendar_events: list Mia calendar holds for a day",
            "- create_calendar_hold: create a tentative calendar hold",
            "- explain_code_request: break down a programming request",
            "- propose_test_cases: propose focused tests for code work",
            "- open_url: open a safe http/https URL in the Mac browser; owner-only",
            "- open_app: request approval to open a macOS app",
            "- read_file: read a local text file",
            "- write_file: request approval to write a local file",
            "- delete_file: request approval to delete a local file",
            "- run_terminal_command: request approval to run a terminal command",
            "- web_search: search the web using SearXNG",
        ]
    )


OWNER_ONLY_TOOLS = {
    "open_url",
    "open_app",
    "read_file",
    "write_file",
    "delete_file",
    "run_terminal_command",
}
