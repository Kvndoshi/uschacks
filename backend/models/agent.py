from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgentStatusEnum(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_HITL = "waiting_hitl"
    COMPLETED = "completed"
    ERROR = "error"


class AgentStatus(BaseModel):
    agent_id: str
    subtask_id: str
    task_description: str
    status: AgentStatusEnum = AgentStatusEnum.IDLE
    current_url: Optional[str] = None
    steps_completed: int = 0
    last_error: Optional[str] = None
    result: Optional[str] = None


class HITLRequest(BaseModel):
    hitl_id: str
    agent_id: str
    action_type: str
    action_description: str
    url: Optional[str] = None
    preview_html: Optional[str] = None


class HITLResolution(BaseModel):
    hitl_id: str
    resolution: str  # approved | rejected | edited
    edited_value: Optional[str] = None
