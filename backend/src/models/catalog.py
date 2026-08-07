"""服务目录与任务相关请求 / 响应模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ServicePriority = Literal["P0", "P1", "P2"]
TaskKind = Literal["skill", "planner", "followup"]
TaskStatus = Literal[
    "pending_approve",
    "processing",
    "need_materials",
    "done",
    "rejected",
    "cancelled",
]
TaskTab = Literal["active", "approve", "history", "planner"]


class ServicePublic(BaseModel):
    id: str
    name: str
    domain: str
    domain_label: str
    priority: ServicePriority
    description: str
    action: str
    can_apply: bool = True


class TaskApplyRequest(BaseModel):
    service_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=200)
    form: Dict[str, Any] = Field(default_factory=dict)


class TaskEventPublic(BaseModel):
    id: str
    time: datetime
    title: str
    desc: str
    done: bool


class TaskPublic(BaseModel):
    id: str
    title: str
    service_id: str
    service_name: str
    domain_label: str
    kind: TaskKind
    status: TaskStatus
    tab: TaskTab
    applicant_name: str
    approver_name: Optional[str] = None
    form: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskPublic):
    events: List[TaskEventPublic] = Field(default_factory=list)


class TaskActionRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=500)
