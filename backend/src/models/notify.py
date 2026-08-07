"""站内消息与用户偏好。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class NotificationPublic(BaseModel):
    id: str
    title: str
    preview: str
    type: Literal["task", "system", "ticket", "material"]
    read: bool
    link: Optional[str] = None
    created_at: datetime


class PreferencePublic(BaseModel):
    language: str = "zh-CN"
    notify_task: bool = True
    notify_ticket: bool = True
    notify_system: bool = False
    auto_handoff: bool = True
    confidence_threshold: float = 0.7


class PreferenceUpdate(BaseModel):
    language: Optional[str] = None
    notify_task: Optional[bool] = None
    notify_ticket: Optional[bool] = None
    notify_system: Optional[bool] = None
    auto_handoff: Optional[bool] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)
