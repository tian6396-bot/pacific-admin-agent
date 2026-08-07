"""转人工工单相关模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

TicketStatus = Literal[
    "waiting",
    "active",
    "need_info",
    "need_expert",
    "resolved",
    "closed",
]
TicketPriority = Literal["normal", "high", "urgent"]
TicketMsgRole = Literal["employee", "agent", "system", "ai"]


class HandoffPackage(BaseModel):
    intent: str = ""
    confidence: float = 0.0
    summary: str = ""
    evidence: List[str] = Field(default_factory=list)
    chat_session_id: Optional[str] = None


class HandoffRequest(BaseModel):
    session_id: Optional[str] = None
    reason: str = Field(default="用户申请转人工", max_length=500)
    priority: TicketPriority = "normal"
    topic: Optional[str] = Field(None, max_length=200)


class TicketMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class TicketMessagePublic(BaseModel):
    id: str
    ticket_id: str
    role: TicketMsgRole
    content: str
    sender_name: str
    created_at: datetime


class TicketPublic(BaseModel):
    id: str
    subject: str
    channel: str
    status: TicketStatus
    priority: TicketPriority
    employee_id: str
    employee_name: str
    employee_dept: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    chat_session_id: Optional[str] = None
    wait_minutes: int = 0
    sla_deadline: Optional[datetime] = None
    sla_overdue: bool = False
    handoff: HandoffPackage = Field(default_factory=HandoffPackage)
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketPublic):
    messages: List[TicketMessagePublic] = Field(default_factory=list)


class QueueKPI(BaseModel):
    waiting: int
    today_claimed: int
    avg_wait_minutes: float
    sla_ok_rate: float


class QueueBoard(BaseModel):
    kpi: QueueKPI
    items: List[TicketPublic]
