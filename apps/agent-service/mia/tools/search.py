import httpx
from langchain_core.tools import StructuredTool


def build_search_tools(*, searxng_base_url: str) -> list[StructuredTool]:
    async def web_search(query: str) -> str:
        if not searxng_base_url:
            return "SearXNG is not configured. Set SEARXNG_BASE_URL to enable web_search."
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{searxng_base_url.rstrip('/')}/search",
                params={"q": query, "format": "json", "language": "en"},
            )
            response.raise_for_status()
            data = response.json()
        results = data.get("results", [])[:5]
        if not results:
            return f"No SearXNG results for: {query}"
        return "\n".join(
            f"{index + 1}. {item.get('title', 'Untitled')} - {item.get('url', '')}\n{item.get('content', '')}"
            for index, item in enumerate(results)
        )

    return [
        StructuredTool.from_function(
            coroutine=web_search,
            name="web_search",
            description="Search the web through the configured SearXNG instance.",
        )
    ]
