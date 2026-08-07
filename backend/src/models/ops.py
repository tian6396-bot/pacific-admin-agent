"""运营配置 / Bad Case / 审计 / 指标模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ConfigStatus = Literal["draft", "published", "offline"]
BadCaseCategory = Literal[
    "intent",
    "knowledge",
    "prompt",
    "tool",
    "flow",
    "permission",
    "experience",
]
BadCaseStatus = Literal["open", "improved", "ignored"]


class IntentPublic(BaseModel):
    id: str
    name: str
    domain: str
    slots: str = ""
    status: ConfigStatus
    prompt_version: str = "v1"
    prompt_content: str = ""
    hit_rate: float = 0.0


class IntentUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    slots: Optional[str] = None
    prompt_version: Optional[str] = None
    prompt_content: Optional[str] = None
    status: Optional[ConfigStatus] = None


class QueueSlaPublic(BaseModel):
    id: str
    name: str
    skill_group: str
    agents: int = 0
    sla_minutes: int = 5
    priority: int = 1
    max_wait: int = 10
    alert_threshold: int = 80
    status: Literal["active", "disabled"] = "active"


class QueueSlaUpdate(BaseModel):
    name: Optional[str] = None
    skill_group: Optional[str] = None
    agents: Optional[int] = None
    sla_minutes: Optional[int] = Field(None, ge=1, le=120)
    priority: Optional[int] = Field(None, ge=1, le=10)
    max_wait: Optional[int] = None
    alert_threshold: Optional[int] = None
    status: Optional[Literal["active", "disabled"]] = None


class BadCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: BadCaseCategory = "experience"
    domain: str = "综合"
    intent: str = ""
    severity: Literal["high", "medium", "low"] = "medium"
    description: str = ""
    root_cause: str = ""
    suggestion: str = ""
    session_id: Optional[str] = None


class BadCaseUpdate(BaseModel):
    status: Optional[BadCaseStatus] = None
    root_cause: Optional[str] = None
    suggestion: Optional[str] = None


class BadCasePublic(BaseModel):
    id: str
    title: str
    category: BadCaseCategory
    domain: str
    intent: str
    severity: Literal["high", "medium", "low"]
    status: BadCaseStatus
    description: str
    root_cause: str
    suggestion: str
    session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuditLogPublic(BaseModel):
    id: str
    operator: str
    role: str
    action: str
    target: str
    ip: str = "127.0.0.1"
    result: Literal["success", "denied"] = "success"
    created_at: datetime


class MetricsSummary(BaseModel):
    sessions_today: int
    ai_resolve_rate: float
    handoff_rate: float
    avg_satisfaction: float
    knowledge_published: int
    tasks_open: int
    tickets_waiting: int
    badcases_open: int
    trend_sessions: List[int] = Field(default_factory=list)
    trend_labels: List[str] = Field(default_factory=list)
