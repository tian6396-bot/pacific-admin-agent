"""Skill / 工具 / 确认闸模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

PublishStatus = Literal["published", "draft", "offline"]
SkillRunStatus = Literal[
    "collecting",
    "awaiting_confirm",
    "running",
    "done",
    "cancelled",
    "failed",
]


class ConfirmCard(BaseModel):
    run_id: str
    skill_id: str
    skill_name: str
    summary: str
    slots: Dict[str, Any] = Field(default_factory=dict)
    mock_tool: bool = True
    tool_name: Optional[str] = None


class SkillPublic(BaseModel):
    id: str
    name: str
    intent: str
    domain: str
    status: PublishStatus
    description: str = ""
    tool_id: Optional[str] = None
    service_id: Optional[str] = None
    priority: str = "P1"


class ToolPublic(BaseModel):
    id: str
    name: str
    method: str
    endpoint: str
    timeout_ms: int = 5000
    retries: int = 1
    status: Literal["active", "disabled"] = "active"
    mock_enabled: bool = True
    schema_json: str = "{}"
    mock_response: str = "{}"


class SkillRunPublic(BaseModel):
    id: str
    skill_id: str
    skill_name: str
    status: SkillRunStatus
    slots: Dict[str, Any] = Field(default_factory=dict)
    confirm_summary: str = ""
    task_id: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirm_card: Optional[ConfirmCard] = None


class SkillConfirmRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=500)


class SkillCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class FlowNodePublic(BaseModel):
    id: str
    type: str
    label: str
    config: str = ""
