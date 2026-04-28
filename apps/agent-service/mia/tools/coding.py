from langchain_core.tools import tool


@tool
def explain_code_request(request: str) -> str:
    """Break down a programming request into concise implementation steps."""
    cleaned = request.strip()
    return f"Implementation outline for: {cleaned}"


@tool
def propose_test_cases(feature: str) -> str:
    """Propose focused test cases for a coding feature or bug fix."""
    return f"Recommended tests: happy path, validation failure, edge input, and regression for {feature}."


CODING_TOOLS = [explain_code_request, propose_test_cases]
