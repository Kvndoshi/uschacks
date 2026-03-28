import asyncio
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from models.task import TaskRequest, TaskResponse, TaskStatus
from mind.queen import execute_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class QueenQueryRequest(BaseModel):
    question: str
    context: str = ""
    agent_id: str
    task_id: str = ""  # optional: used to look up per-task memory


# task_id -> TaskResponse for completed/failed tasks
active_tasks: dict[str, TaskResponse] = {}

# task_id -> status string for in-progress tasks
_running_tasks: dict[str, str] = {}


@router.post("/submit", response_model=TaskResponse)
async def submit_task(request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    _running_tasks[task_id] = TaskStatus.DECOMPOSING

    async def _run():
        from services.websocket_manager import manager as ws_manager
        from models import events
        _running_tasks[task_id] = TaskStatus.RUNNING
        try:
            result = await execute_task(request, task_id=task_id)
            active_tasks[result.task_id] = result
            _running_tasks.pop(task_id, None)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            _running_tasks.pop(task_id, None)
            failed_response = TaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                subtasks=[],
                results=[],
                final_result=f"Task failed: {e}",
            )
            active_tasks[task_id] = failed_response
            # Broadcast TASK_FAILED event so frontend is notified
            await ws_manager.broadcast(events.task_failed(
                task_id, str(e), master_task=request.task))

    background_tasks.add_task(_run)

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.DECOMPOSING,
        subtasks=[],
        results=[],
        final_result=None,
    )


@router.get("/active")
async def get_active_tasks():
    """List all currently running task IDs and their live status."""
    running = [
        {"task_id": tid, "status": status}
        for tid, status in _running_tasks.items()
    ]
    return {"active_tasks": running, "count": len(running)}


@router.post("/queen-query")
async def queen_query(req: QueenQueryRequest):
    """Ask the Queen for guidance (used by workers when stuck)."""
    from mind.queen import answer_query
    from mind.memory import get_memory, get_active_memory
    # Prefer per-task memory; fall back to the global latest memory
    memory = (get_memory(req.task_id) if req.task_id else None) or get_active_memory()
    answer = await answer_query(
        req.question, req.context, req.agent_id,
        memory=memory, task_id=req.task_id,
    )
    return {"answer": answer}


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    if task_id in active_tasks:
        return active_tasks[task_id]
    # Return live status if still running
    if task_id in _running_tasks:
        return TaskResponse(
            task_id=task_id,
            status=_running_tasks[task_id],
            subtasks=[],
            results=[],
        )
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.RUNNING,
        subtasks=[],
        results=[],
    )
