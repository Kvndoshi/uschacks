from typing import TypedDict, Optional
from models.task import SubTask, SubTaskResult


class WorkerState(TypedDict):
    agent_id: str
    subtask_id: str
    task_description: str
    status: str
    current_url: str
    actions_taken: list[dict]
    pending_hitl: Optional[dict]
    hitl_history: list[dict]
    steps_completed: int
    last_error: str
    result: str


class MindState(TypedDict):
    task_id: str
    master_task: str
    decomposition_reasoning: str
    subtasks: list[dict]
    assignment_map: dict[str, str]
    worker_results: dict[str, str]
    final_result: str
    phase: str
    errors: list[str]
