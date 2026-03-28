import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional
from models.task import SubTaskResult

logger = logging.getLogger(__name__)

# Registry of all active task memories, keyed by task_id
_task_memories: dict[str, "SharedMindMemory"] = {}
# Track insertion order so get_active_memory() can return the latest
_task_order: list[str] = []


@dataclass
class SharedMindMemory:
    task_id: str = ""
    master_task: str = ""
    task_context: str = ""
    completed_subtasks: list[SubTaskResult] = field(default_factory=list)
    discovered_facts: list[str] = field(default_factory=list)
    global_errors: list[str] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_result(self, result: SubTaskResult):
        async with self.lock:
            self.completed_subtasks.append(result)

    async def add_fact(self, fact: str):
        async with self.lock:
            self.discovered_facts.append(fact)
        try:
            from services import supermemory_service
            await supermemory_service.save_memory(
                content=fact,
                metadata={"type": "discovered_fact", "task_id": self.task_id},
            )
        except Exception as e:
            logger.debug("Supermemory fact save skipped: %s", e)

    async def add_error(self, error: str):
        async with self.lock:
            self.global_errors.append(error)

    async def get_context_summary(self) -> str:
        """Thread-safe async context summary."""
        async with self.lock:
            parts = [f"Master task: {self.master_task}"]
            if self.task_context:
                parts.append(f"Context: {self.task_context}")
            if self.discovered_facts:
                parts.append(f"Discovered facts: {'; '.join(self.discovered_facts[-5:])}")
            if self.completed_subtasks:
                parts.append(f"Completed: {len(self.completed_subtasks)} subtasks")
        return "\n".join(parts)

    def get_context_summary_sync(self) -> str:
        """Synchronous fallback for callers that cannot await (use sparingly)."""
        parts = [f"Master task: {self.master_task}"]
        if self.task_context:
            parts.append(f"Context: {self.task_context}")
        if self.discovered_facts:
            parts.append(f"Discovered facts: {'; '.join(self.discovered_facts[-5:])}")
        if self.completed_subtasks:
            parts.append(f"Completed: {len(self.completed_subtasks)} subtasks")
        return "\n".join(parts)


def get_memory(task_id: str) -> Optional[SharedMindMemory]:
    """Look up memory for a specific task_id. Returns None if not found."""
    return _task_memories.get(task_id)


def create_memory(task_id: str, master_task: str, context: str = "") -> SharedMindMemory:
    """Create, store, and return a new SharedMindMemory for the given task_id."""
    mem = SharedMindMemory(
        task_id=task_id,
        master_task=master_task,
        task_context=context,
    )
    _task_memories[task_id] = mem
    if task_id in _task_order:
        _task_order.remove(task_id)
    _task_order.append(task_id)
    logger.debug("Created memory for task %s", task_id)
    return mem


def get_active_memory() -> Optional[SharedMindMemory]:
    """Return the most recently created memory (backward compat)."""
    if _task_order:
        return _task_memories.get(_task_order[-1])
    return None


# ---------------------------------------------------------------------------
# Backward-compatible shims — keep code that imports `mind_memory` working
# ---------------------------------------------------------------------------

def _get_latest_memory() -> "SharedMindMemory":
    """Internal helper that always returns *some* memory (creating a default if empty)."""
    mem = get_active_memory()
    if mem is None:
        mem = create_memory("default", "")
    return mem


class _MemoryProxy:
    """Proxy object so that ``from mind.memory import mind_memory`` still works.
    Attribute accesses / async method calls are forwarded to the latest memory."""

    def __getattr__(self, name: str):
        return getattr(_get_latest_memory(), name)

    def __setattr__(self, name: str, value):
        setattr(_get_latest_memory(), name, value)


# Module-level ``mind_memory`` alias used by legacy code
mind_memory: SharedMindMemory = _MemoryProxy()  # type: ignore[assignment]


def reset_memory(task_id: str, master_task: str, context: str = "") -> SharedMindMemory:
    """Backward-compatible reset — creates a new memory via create_memory()."""
    return create_memory(task_id, master_task, context)
