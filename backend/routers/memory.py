import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services import supermemory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class MemorySaveRequest(BaseModel):
    content: str
    metadata: Optional[dict] = None


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/save")
async def save_memory(req: MemorySaveRequest):
    doc_id = await supermemory_service.save_memory(req.content, req.metadata)
    if doc_id:
        return {"ok": True, "id": doc_id}
    return {"ok": False, "error": "Save failed"}


@router.post("/search")
async def search_memory(req: MemorySearchRequest):
    results = await supermemory_service.search_memory(req.query, req.limit)
    return {"ok": True, "results": results, "count": len(results)}


@router.get("/health")
async def memory_health():
    """Check if supermemory is configured and reachable."""
    from config import SUPERMEMORY_API_KEY
    if not SUPERMEMORY_API_KEY:
        return {"ok": False, "error": "SUPERMEMORY_API_KEY not set"}
    try:
        results = await supermemory_service.search_memory("test", limit=1)
        return {"ok": True, "tag": supermemory_service.CONTAINER_TAG}
    except Exception as e:
        return {"ok": False, "error": str(e)}
