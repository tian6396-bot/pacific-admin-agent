"""材料中心模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

MaterialStatus = Literal["pending", "parsing", "success", "failed"]


class MaterialPublic(BaseModel):
    id: str
    filename: str
    content_type: str = ""
    size: int = 0
    size_label: str = ""
    file_kind: str = ""
    status: MaterialStatus
    parse_text: Optional[str] = None
    error: Optional[str] = None
    task_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MaterialLinkUpdate(BaseModel):
    task_id: Optional[str] = Field(None, max_length=36)
