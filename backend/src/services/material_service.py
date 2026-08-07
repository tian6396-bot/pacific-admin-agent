"""材料上传与简易解析。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import BACKEND_ROOT, settings
from src.db.models import Material, User
from src.models.material import MaterialLinkUpdate, MaterialPublic
from src.repositories.material import MaterialRepository
from src.services.knowledge_pipeline import extract_text_from_pdf

logger = get_logger()

MAX_BYTES = 10 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _materials_root() -> Path:
    path = Path(settings.upload_dir) / "materials"
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _size_label(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _file_kind(filename: str, content_type: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf" or "pdf" in content_type:
        return "PDF"
    if ext in {".jpg", ".jpeg", ".png", ".webp"} or content_type.startswith("image/"):
        return "图片"
    return ext.lstrip(".").upper() or "文件"


class MaterialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MaterialRepository(db)

    def to_public(self, row: Material) -> MaterialPublic:
        return MaterialPublic(
            id=row.id,
            filename=row.filename,
            content_type=row.content_type,
            size=row.size,
            size_label=_size_label(row.size),
            file_kind=_file_kind(row.filename, row.content_type),
            status=row.status,  # type: ignore[arg-type]
            parse_text=row.parse_text,
            error=row.error,
            task_id=row.task_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_mine(self, user: User) -> list[MaterialPublic]:
        rows = await self.repo.list_for_user(user.id, is_admin=user.role == "admin")
        return [self.to_public(r) for r in rows]

    async def upload(
        self,
        user: User,
        *,
        filename: str,
        content_type: str,
        raw: bytes,
        task_id: str | None = None,
    ) -> MaterialPublic:
        if not raw:
            raise ValueError("空文件")
        if len(raw) > MAX_BYTES:
            raise ValueError("文件超过 10MB 限制")
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise ValueError("仅支持 PDF / JPG / PNG / WEBP")

        mid = str(uuid.uuid4())
        dest = _materials_root() / f"{mid}{ext}"
        dest.write_bytes(raw)

        row = Material(
            id=mid,
            user_id=user.id,
            filename=filename,
            content_type=content_type or "",
            size=len(raw),
            path=str(dest),
            status="pending",
            task_id=task_id,
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.add(row)
        await self._parse(row)
        logger.info("Material uploaded", material_id=mid, status=row.status)
        return self.to_public(row)

    async def _parse(self, row: Material) -> None:
        row.status = "parsing"
        row.error = None
        row.updated_at = _now()
        await self.db.flush()

        path = Path(row.path)
        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                text = extract_text_from_pdf(path)
                row.parse_text = text[:4000]
                row.status = "success"
            elif ext in {".jpg", ".jpeg", ".png", ".webp"}:
                # MVP：图片不做真 OCR，记元数据即成功
                row.parse_text = f"[图片材料] {row.filename}（演示环境未启用 OCR，已登记元数据）"
                row.status = "success"
            else:
                raise ValueError("不支持的文件类型")
        except Exception as exc:  # noqa: BLE001
            row.status = "failed"
            row.error = str(exc)[:500]
            row.parse_text = None
            logger.warning("Material parse failed", material_id=row.id, error=str(exc))
        row.updated_at = _now()
        await self.db.flush()

    async def retry(self, user: User, material_id: str) -> MaterialPublic:
        row = await self.repo.get(material_id)
        if row is None:
            raise FileNotFoundError("材料不存在")
        if row.user_id != user.id and user.role != "admin":
            raise PermissionError("无权操作该材料")
        if row.status not in ("failed", "success"):
            raise ValueError("当前状态不可重试")
        await self._parse(row)
        return self.to_public(row)

    async def link_task(
        self, user: User, material_id: str, body: MaterialLinkUpdate
    ) -> MaterialPublic:
        row = await self.repo.get(material_id)
        if row is None:
            raise FileNotFoundError("材料不存在")
        if row.user_id != user.id and user.role != "admin":
            raise PermissionError("无权操作该材料")
        row.task_id = body.task_id
        row.updated_at = _now()
        await self.db.flush()
        return self.to_public(row)
