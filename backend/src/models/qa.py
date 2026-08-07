"""质检与回访模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

FollowupStatus = Literal["pending", "done", "overdue"]


class QaItemScore(BaseModel):
    label: str
    score: int
    max: int = 25


class QaRecordCreate(BaseModel):
    ticket_id: Optional[str] = None
    session_label: str = ""
    agent_name: str = Field(..., min_length=1, max_length=100)
    items: List[QaItemScore] = Field(default_factory=list)
    reviewer: str = ""


class QaRecordPublic(BaseModel):
    id: str
    ticket_id: Optional[str] = None
    session_label: str
    agent_name: str
    score: int
    items: List[QaItemScore]
    reviewer: str
    created_at: datetime


class FollowupUpdate(BaseModel):
    status: Optional[FollowupStatus] = None
    assignee: Optional[str] = None


class FollowupPublic(BaseModel):
    id: str
    employee_name: str
    type: str
    due_date: str
    status: FollowupStatus
    assignee: str
    ticket_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
