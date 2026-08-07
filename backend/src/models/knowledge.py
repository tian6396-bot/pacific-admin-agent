"""知识发布 / 检索相关请求与响应模型。"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

KnowledgeType = Literal["faq", "doc"]
KnowledgeStatus = Literal["draft", "review", "published", "offline"]


class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    type: KnowledgeType = "faq"
    category: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, description="FAQ 答案或文档正文")
    version: str = Field(default="v1", max_length=32)
    permission_tags: str = Field(default="全员可读", max_length=200)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = None
    version: Optional[str] = Field(None, max_length=32)
    permission_tags: Optional[str] = Field(None, max_length=200)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class ChunkUpdate(BaseModel):
    text: str = Field(..., min_length=1)


class ChunkPublic(BaseModel):
    id: str
    index: int
    text: str
    confidence: float
    needs_review: bool


class KnowledgePublic(BaseModel):
    id: str
    title: str
    type: KnowledgeType
    category: str
    status: KnowledgeStatus
    version: str
    author: str
    updated_at: datetime
    permission_tags: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    source_filename: Optional[str] = None
    content: Optional[str] = None
    chunk_count: int = 0
    low_confidence_count: int = 0


class KnowledgeDetail(KnowledgePublic):
    chunks: List[ChunkPublic] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    category: str
    text: str
    score: float
    version: str


class SearchResponse(BaseModel):
    hits: List[SearchHit]
    mode: str = Field(description="vector | keyword | hybrid")
