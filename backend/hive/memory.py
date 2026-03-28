import asyncio
from dataclasses import dataclass, field
from models.task import SubTaskResult


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

    async def add_error(self, error: str):
        async with self.lock:
            self.global_errors.append(error)

    def get_context_summary(self) -> str:
        parts = [f"Master task: {self.master_task}"]
        if self.task_context:
            parts.append(f"Context: {self.task_context}")
        if self.discovered_facts:
            parts.append(f"Discovered facts: {'; '.join(self.discovered_facts[-5:])}")
        if self.completed_subtasks:
            parts.append(f"Completed: {len(self.completed_subtasks)} subtasks")
        return "\n".join(parts)


mind_memory = SharedMindMemory()


def reset_memory(task_id: str, master_task: str, context: str = ""):
    global mind_memory
    mind_memory = SharedMindMemory(
        task_id=task_id,
        master_task=master_task,
        task_context=context,
    )
    return mind_memory
