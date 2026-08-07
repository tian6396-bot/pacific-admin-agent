"""对话会话 / 消息相关请求与响应模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from src.models.skill import ConfirmCard

MessageRole = Literal["user", "assistant", "system"]
RouteType = Literal[
    "qa_direct",
    "qa_rag",
    "clarify",
    "skill",
    "human_review",
    "web",
    "fallback",
]


class Citation(BaseModel):
    document_id: str
    title: str
    text: str
    score: float = 0.0
    version: str = ""


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class MessagePublic(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    citations: List[Citation] = Field(default_factory=list)
    route: Optional[str] = None
    created_at: datetime
    confirm_card: Optional[ConfirmCard] = None


class SessionPublic(BaseModel):
    id: str
    title: str
    updated_at: datetime
    created_at: datetime
    preview: Optional[str] = None


class SessionDetail(SessionPublic):
    messages: List[MessagePublic] = Field(default_factory=list)


class ChatReply(BaseModel):
    session: SessionPublic
    user_message: MessagePublic
    assistant_message: MessagePublic
    confirm_card: Optional[ConfirmCard] = None
