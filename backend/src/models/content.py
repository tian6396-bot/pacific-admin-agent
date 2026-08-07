"""内容产出：改写 / 报告 / 数据导出。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ContentKind = Literal["rewrite", "report", "export"]
ExportDataset = Literal[
    "my_tasks",
    "my_tickets",
    "agent_tickets",
    "qa_followups",
    "knowledge",
    "bad_cases",
    "audit_logs",
]
Tone = Literal["formal", "concise", "friendly"]


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=12000)
    tone: Tone = "formal"
    title: str = Field(default="文档改写", max_length=120)


class ReportRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    points: str = Field(default="", max_length=4000)
    title: str = Field(default="报告草稿", max_length=120)


class ExportRequest(BaseModel):
    dataset: ExportDataset
    title: str = Field(default="数据导出", max_length=120)


class ContentArtifactPublic(BaseModel):
    id: str
    kind: ContentKind
    title: str
    summary: str
    body: str
    mime: str
    download_name: str
    task_id: str | None = None
    owner_role: str
    created_at: datetime
    has_pptx: bool = False
    pptx_name: str | None = None


class ContentCapabilities(BaseModel):
    can_rewrite: bool
    can_report: bool
    can_pptx: bool
    export_datasets: list[ExportDataset]
    notes: list[str]
