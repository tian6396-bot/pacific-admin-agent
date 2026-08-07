"""知识管理路由。"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession, require_roles
from src.db.models import User
from src.models.knowledge import ChunkUpdate, KnowledgeCreate, KnowledgeUpdate, SearchRequest
from src.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

AdminUser = Annotated[User, Depends(require_roles("admin"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (ValueError, RuntimeError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("")
async def list_knowledge(
    db: DbSession,
    user: CurrentUser,
    type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
):
    _ = user
    items = await KnowledgeService(db).list(type_=type, status=status_filter)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("")
async def create_knowledge(body: KnowledgeCreate, db: DbSession, user: AdminUser):
    try:
        detail = await KnowledgeService(db).create(body, user)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="创建成功")


@router.post("/upload")
async def upload_knowledge(
    db: DbSession,
    user: AdminUser,
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("未分类"),
    version: str = Form("v1"),
    permission_tags: str = Form("全员可读"),
    effective_from: str | None = Form(None),
    effective_to: str | None = Form(None),
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")

    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)

    try:
        detail = await KnowledgeService(db).upload_pdf(
            file_bytes=raw,
            filename=file.filename or "upload.pdf",
            title=title,
            category=category,
            user=user,
            version=version,
            permission_tags=permission_tags,
            effective_from=_parse_date(effective_from),
            effective_to=_parse_date(effective_to),
        )
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="上传并解析成功")


@router.post("/search")
async def search_knowledge(body: SearchRequest, db: DbSession, user: CurrentUser):
    _ = user
    result = await KnowledgeService(db).search(body)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{doc_id}")
async def get_knowledge(doc_id: str, db: DbSession, user: CurrentUser):
    _ = user
    try:
        detail = await KnowledgeService(db).get(doc_id)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"))


@router.patch("/{doc_id}")
async def update_knowledge(doc_id: str, body: KnowledgeUpdate, db: DbSession, user: AdminUser):
    _ = user
    try:
        detail = await KnowledgeService(db).update(doc_id, body)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已更新")


@router.patch("/{doc_id}/chunks/{chunk_id}")
async def update_chunk(
    doc_id: str,
    chunk_id: str,
    body: ChunkUpdate,
    db: DbSession,
    user: AdminUser,
):
    _ = user
    try:
        chunk = await KnowledgeService(db).update_chunk(doc_id, chunk_id, body)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=chunk.model_dump(mode="json"), message="Chunk 已校对")


@router.post("/{doc_id}/submit")
async def submit_knowledge(doc_id: str, db: DbSession, user: AdminUser):
    _ = user
    try:
        detail = await KnowledgeService(db).submit(doc_id)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已提交审核")


@router.post("/{doc_id}/publish")
async def publish_knowledge(doc_id: str, db: DbSession, user: AdminUser):
    try:
        detail = await KnowledgeService(db).publish(doc_id)
        from src.services.ops_service import write_audit

        await write_audit(
            db,
            user,
            action="发布知识",
            target=f"{detail.id} {detail.title}",
        )
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已发布")


@router.post("/{doc_id}/offline")
async def offline_knowledge(doc_id: str, db: DbSession, user: AdminUser):
    _ = user
    try:
        detail = await KnowledgeService(db).offline(doc_id)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已下线")


@router.post("/{doc_id}/reindex")
async def reindex_knowledge(doc_id: str, db: DbSession, user: AdminUser):
    _ = user
    try:
        detail = await KnowledgeService(db).reindex(doc_id)
    except (FileNotFoundError, ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已重建 Chunk")
