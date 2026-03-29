import logging
from typing import Optional
from supermemory import AsyncSupermemory
from config import SUPERMEMORY_API_KEY

logger = logging.getLogger(__name__)

CONTAINER_TAG = "hivemind"

_client: Optional[AsyncSupermemory] = None


def _get_client() -> AsyncSupermemory:
    global _client
    if _client is None:
        if not SUPERMEMORY_API_KEY:
            raise RuntimeError("SUPERMEMORY_API_KEY not set")
        _client = AsyncSupermemory(api_key=SUPERMEMORY_API_KEY)
    return _client


async def save_memory(
    content: str,
    metadata: Optional[dict] = None,
    custom_id: Optional[str] = None,
) -> Optional[str]:
    """Save content to supermemory under the hivemind tag. Returns doc id."""
    try:
        client = _get_client()
        kwargs: dict = {
            "content": content,
            "container_tags": [CONTAINER_TAG],
        }
        if metadata:
            clean = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
            if clean:
                kwargs["metadata"] = clean
        if custom_id:
            kwargs["custom_id"] = custom_id

        result = await client.documents.add(**kwargs)
        doc_id = getattr(result, "id", None) or str(result)
        logger.info("Supermemory saved (id=%s): %s", doc_id, content[:80])
        return doc_id
    except Exception as e:
        logger.error("Supermemory save failed: %s", e)
        return None


async def search_memory(query: str, limit: int = 5) -> list[dict]:
    """Search supermemory for relevant memories. Returns list of result dicts."""
    try:
        client = _get_client()
        response = await client.search.execute(
            q=query,
            limit=limit,
            container_tags=[CONTAINER_TAG],
            include_summary=True,
        )
        results = []
        for r in response.results:
            chunks_text = ""
            if hasattr(r, "chunks") and r.chunks:
                chunks_text = "\n".join(
                    getattr(c, "content", str(c)) for c in r.chunks if getattr(c, "is_relevant", True)
                )
            results.append({
                "id": getattr(r, "document_id", ""),
                "score": getattr(r, "score", 0),
                "title": getattr(r, "title", ""),
                "summary": getattr(r, "summary", ""),
                "content": chunks_text or getattr(r, "content", ""),
            })
        logger.info("Supermemory search '%s': %d results", query[:40], len(results))
        return results
    except Exception as e:
        logger.error("Supermemory search failed: %s", e)
        return []


async def save_task_execution(task: str, result: str, agent_count: int, task_id: str) -> Optional[str]:
    """Save a completed task's input and output to supermemory."""
    content = f"Task: {task}\n\nResult:\n{result}"
    return await save_memory(
        content=content,
        metadata={
            "type": "task_execution",
            "agent_count": agent_count,
            "task_id": task_id,
        },
        custom_id=f"task-{task_id}",
    )


async def save_chat_exchange(user_message: str, assistant_reply: str) -> Optional[str]:
    """Save a chat exchange to supermemory."""
    content = f"User: {user_message}\n\nAssistant: {assistant_reply}"
    return await save_memory(
        content=content,
        metadata={"type": "chat"},
    )


async def save_page_fact(url: str, title: str, content_preview: str) -> Optional[str]:
    """Save a captured page fact to supermemory."""
    content = f"Saved page: {title}\nURL: {url}\nContent: {content_preview}"
    return await save_memory(
        content=content,
        metadata={"type": "page_capture", "url": url},
    )
