"""
Tavily Search — web search fallback used when retrieved context is thin.
"""

from __future__ import annotations

import httpx
from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


async def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
) -> list[dict]:
    """
    Perform a web search via Tavily API.

    Returns a list of result dicts:
    {
        "title": str,
        "url": str,
        "content": str,   # snippet
        "score": float
    }
    """
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(TAVILY_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            log.info("tavily_search_done", query=query[:60], results=len(results))
            return results
    except Exception as exc:
        log.error("tavily_search_error", error=str(exc))
        return []
