"""内容产出 API：改写 / 报告 / 导出。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.content import ExportRequest, ReportRequest, RewriteRequest
from src.services.content_service import ContentService

router = APIRouter(prefix="/content", tags=["content"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/capabilities")
async def get_capabilities(db: DbSession, user: CurrentUser):
    caps = ContentService(db).capabilities(user)
    return success_response(data=caps.model_dump(mode="json"))


@router.get("/artifacts")
async def list_artifacts(db: DbSession, user: CurrentUser):
    items = await ContentService(db).list_mine(user)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, db: DbSession, user: CurrentUser):
    try:
        item = await ContentService(db).get_mine(user, artifact_id)
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"))


@router.post("/rewrite")
async def rewrite(body: RewriteRequest, db: DbSession, user: CurrentUser):
    try:
        item = await ContentService(db).rewrite(user, body)
    except (PermissionError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="改写完成")


@router.post("/report")
async def report(body: ReportRequest, db: DbSession, user: CurrentUser):
    try:
        item = await ContentService(db).report(user, body)
    except (PermissionError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="报告已生成")


@router.post("/export")
async def export_data(body: ExportRequest, db: DbSession, user: CurrentUser):
    try:
        item = await ContentService(db).export(user, body)
    except (PermissionError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="导出完成")
