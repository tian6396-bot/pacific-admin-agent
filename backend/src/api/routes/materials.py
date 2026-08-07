"""材料中心路由。"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.material import MaterialLinkUpdate
from src.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["materials"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("")
async def list_materials(db: DbSession, user: CurrentUser):
    items = await MaterialService(db).list_mine(user)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("")
async def upload_material(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    task_id: str | None = Form(None),
):
    raw = await file.read()
    try:
        item = await MaterialService(db).upload(
            user,
            filename=file.filename or "upload.bin",
            content_type=file.content_type or "",
            raw=raw,
            task_id=task_id or None,
        )
    except (ValueError, RuntimeError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="上传成功")


@router.post("/{material_id}/retry")
async def retry_material(material_id: str, db: DbSession, user: CurrentUser):
    try:
        item = await MaterialService(db).retry(user, material_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="已重新解析")


@router.patch("/{material_id}")
async def link_material(
    material_id: str, body: MaterialLinkUpdate, db: DbSession, user: CurrentUser
):
    try:
        item = await MaterialService(db).link_task(user, material_id, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="已更新关联")
