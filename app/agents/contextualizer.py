from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.models.llm import call_llm
from app.utils.logger import get_logger

log = get_logger(__name__)

CONTEXTUALIZE_SYSTEM = """You rewrite a user's latest message into a standalone question, \
using the conversation history for context. Do not answer the question. \
Do not add medical advice. Output ONLY the rewritten question as plain text, nothing else. \
If the message is already standalone, return it unchanged."""

CONTEXTUALIZE_USER = """Conversation history:
{history}

Latest message: {query}

Standalone question:"""


async def contextualize_query(query: str, history: list[dict]) -> str:
    if not history:
        return query

    last_turns = history[-4:]
    history_text = "\n".join(f"{h.get('role', 'user')}: {h.get('content', '')[:200]}" for h in last_turns)

    messages = [
        SystemMessage(content=CONTEXTUALIZE_SYSTEM),
        HumanMessage(content=CONTEXTUALIZE_USER.format(history=history_text, query=query)),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.emergency_model,   # reuse the fast Groq lane, cheap + low latency
            max_tokens=80,
            force_json=False,
            lane="emergency",                 # reuse emergency's semaphore, it's lightly loaded
        )
        rewritten = response.content.strip() if response else query
        log.info("query_contextualized", original=query[:80], rewritten=rewritten[:80])
        return rewritten or query
    except Exception as exc:
        log.warning("contextualize_failed", error=str(exc))
        return query  # fail-safe: fall back to raw query
