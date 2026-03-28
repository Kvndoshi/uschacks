import asyncio
import uuid
import logging
from models.task import SubTask, TaskRequest, TaskResponse, TaskStatus
from models import events
from hive.memory import reset_memory, mind_memory
from hive.worker import run_worker
from services.mistral_client import queen_decompose
from services.websocket_manager import manager as ws_manager
from services import elevenlabs_service

logger = logging.getLogger(__name__)


async def execute_task(request: TaskRequest) -> TaskResponse:
    task_id = str(uuid.uuid4())[:8]
    memory = reset_memory(task_id, request.task, request.context or "")

    logger.info(f"Task {task_id}: Decomposing '{request.task[:60]}'")

    raw_subtasks = await queen_decompose(request.task, request.context or "")

    subtasks = []
    for i, raw in enumerate(raw_subtasks):
        st = SubTask(
            description=raw.get("description", ""),
            url=raw.get("url"),
            depends_on=raw.get("depends_on", []),
            priority=raw.get("priority", 1),
        )
        subtasks.append(st)

    await ws_manager.broadcast(events.task_accepted(task_id, len(subtasks)))

    try:
        audio = await elevenlabs_service.announce(
            f"Mind activated. Spawning {len(subtasks)} agents.")
        if audio:
            await ws_manager.broadcast(events.voice_announcement(
                f"Mind activated. Spawning {len(subtasks)} agents.", audio))
    except Exception:
        pass

    independent = [st for st in subtasks if not st.depends_on]
    dependent = [st for st in subtasks if st.depends_on]

    tasks = []
    for i, st in enumerate(independent):
        tasks.append(run_worker(st, i))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    if dependent:
        dep_tasks = []
        for i, st in enumerate(dependent):
            dep_tasks.append(run_worker(st, len(independent) + i))
        dep_results = await asyncio.gather(*dep_tasks, return_exceptions=True)
        results = list(results) + list(dep_results)

    successful = []
    failed = []
    for r in results:
        if isinstance(r, Exception):
            failed.append(str(r))
        elif r.success:
            successful.append(r)
        else:
            failed.append(r.result)

    if successful:
        final_result = "\n\n".join([
            f"**Subtask {r.subtask_id}** ({r.steps_taken} steps):\n{r.result}"
            for r in successful
        ])
    else:
        final_result = "All subtasks failed: " + "; ".join(failed)

    status = TaskStatus.COMPLETED if successful else TaskStatus.FAILED

    await ws_manager.broadcast(events.task_complete(task_id, final_result))

    try:
        audio = await elevenlabs_service.announce("All tasks complete. Results are ready.")
        if audio:
            await ws_manager.broadcast(events.voice_announcement(
                "All tasks complete. Results are ready.", audio))
    except Exception:
        pass

    return TaskResponse(
        task_id=task_id,
        status=status,
        subtasks=subtasks,
        results=list(successful),
        final_result=final_result,
    )


async def execute_tab_tasks(tabs_with_instructions: list, global_task: str = ""):
    """Execute per-tab instructions in parallel. Each tab gets its own worker."""
    task_id = str(uuid.uuid4())[:8]
    tab_count = len(tabs_with_instructions)

    reset_memory(task_id, global_task or "Tab-based parallel execution")

    await ws_manager.broadcast(events.task_accepted(task_id, tab_count))

    try:
        audio = await elevenlabs_service.announce(
            f"Mind activated. Executing on {tab_count} tabs in parallel.")
        if audio:
            await ws_manager.broadcast(events.voice_announcement(
                f"Mind activated. Executing on {tab_count} tabs in parallel.", audio))
    except Exception:
        pass

    subtasks = []
    for tab in tabs_with_instructions:
        url = tab.url if hasattr(tab, "url") else ""
        instruction = tab.instruction if hasattr(tab, "instruction") else str(tab)
        tab_id = tab.tab_id if hasattr(tab, "tab_id") else ""

        task_desc = instruction
        if url and url != "about:blank":
            task_desc = f"On the page at {url}: {instruction}"

        st = SubTask(
            description=task_desc,
            url=url if url != "about:blank" else None,
        )
        subtasks.append((st, tab_id))

    worker_tasks = []
    for i, (st, tab_id) in enumerate(subtasks):
        worker_tasks.append(run_worker(st, i))

    results = await asyncio.gather(*worker_tasks, return_exceptions=True)

    successful = []
    failed_list = []
    for r in results:
        if isinstance(r, Exception):
            failed_list.append(str(r))
        elif r.success:
            successful.append(r)
        else:
            failed_list.append(r.result)

    if successful:
        final_result = "\n\n".join([
            f"**Tab task {r.subtask_id}** ({r.steps_taken} steps):\n{r.result}"
            for r in successful
        ])
    else:
        final_result = "All tab tasks failed: " + "; ".join(failed_list)

    await ws_manager.broadcast(events.task_complete(task_id, final_result))

    try:
        audio = await elevenlabs_service.announce("All tab tasks complete. Results are ready.")
        if audio:
            await ws_manager.broadcast(events.voice_announcement(
                "All tab tasks complete. Results are ready.", audio))
    except Exception:
        pass
