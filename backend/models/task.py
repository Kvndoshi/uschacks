from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SubTask(BaseModel):
    subtask_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    url: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    priority: int = 1


class TaskRequest(BaseModel):
    task: str
    context: Optional[str] = None


class SubTaskResult(BaseModel):
    subtask_id: str
    agent_id: str
    result: str
    steps_taken: int = 0
    success: bool = True


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    subtasks: list[SubTask] = Field(default_factory=list)
    results: list[SubTaskResult] = Field(default_factory=list)
    final_result: Optional[str] = None
