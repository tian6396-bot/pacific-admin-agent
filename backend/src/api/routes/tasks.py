"""任务路由。"""

from fastapi import APIRouter, HTTPException, Query, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.catalog import TaskActionRequest, TaskApplyRequest
from src.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("")
async def list_tasks(
    db: DbSession,
    user: CurrentUser,
    tab: str | None = Query(default=None),
):
    items = await TaskService(db).list(user, tab=tab)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("")
async def apply_task(body: TaskApplyRequest, db: DbSession, user: CurrentUser):
    try:
        detail = await TaskService(db).apply(user, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="申请已提交")


@router.get("/{task_id}")
async def get_task(task_id: str, db: DbSession, user: CurrentUser):
    try:
        detail = await TaskService(db).get(user, task_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"))


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    db: DbSession,
    user: CurrentUser,
    body: TaskActionRequest = TaskActionRequest(),
):
    try:
        detail = await TaskService(db).approve(user, task_id, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已通过")


@router.post("/{task_id}/reject")
async def reject_task(
    task_id: str,
    db: DbSession,
    user: CurrentUser,
    body: TaskActionRequest = TaskActionRequest(),
):
    try:
        detail = await TaskService(db).reject(user, task_id, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已驳回")


@router.post("/{task_id}/request-materials")
async def request_materials(task_id: str, db: DbSession, user: CurrentUser):
    try:
        detail = await TaskService(db).request_materials(user, task_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已标记待补充材料")
