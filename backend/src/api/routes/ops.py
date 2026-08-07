"""运营配置 / 洞察 / 审计路由（admin only）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from pycore.api.responses import success_response
from src.api.deps import DbSession, require_roles
from src.db.models import User
from src.models.ops import BadCaseCreate, BadCaseUpdate, IntentUpdate, QueueSlaUpdate
from src.services.ops_service import OpsService

router = APIRouter(prefix="/ops", tags=["ops"])
AdminUser = Annotated[User, Depends(require_roles("admin"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/intents")
async def list_intents(db: DbSession, user: AdminUser):
    _ = user
    items = await OpsService(db).list_intents()
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.patch("/intents/{intent_id}")
async def update_intent(
    intent_id: str, body: IntentUpdate, db: DbSession, user: AdminUser
):
    try:
        item = await OpsService(db).update_intent(user, intent_id, body)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="意图已更新")


@router.post("/intents/{intent_id}/publish")
async def publish_intent(intent_id: str, db: DbSession, user: AdminUser):
    try:
        item = await OpsService(db).publish_intent(user, intent_id)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="意图已发布")


@router.post("/intents/{intent_id}/offline")
async def offline_intent(intent_id: str, db: DbSession, user: AdminUser):
    try:
        item = await OpsService(db).offline_intent(user, intent_id)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="意图已下线")


@router.get("/queues")
async def list_queues(db: DbSession, user: AdminUser):
    _ = user
    items = await OpsService(db).list_queues()
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.patch("/queues/{queue_id}")
async def update_queue(
    queue_id: str, body: QueueSlaUpdate, db: DbSession, user: AdminUser
):
    try:
        item = await OpsService(db).update_queue(user, queue_id, body)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="SLA 已保存")


@router.get("/badcases")
async def list_badcases(
    db: DbSession,
    user: AdminUser,
    domain: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    _ = user
    items = await OpsService(db).list_badcases(domain=domain, status=status_filter)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("/badcases")
async def create_badcase(body: BadCaseCreate, db: DbSession, user: AdminUser):
    try:
        item = await OpsService(db).create_badcase(user, body)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="Bad Case 已登记")


@router.patch("/badcases/{case_id}")
async def update_badcase(
    case_id: str, body: BadCaseUpdate, db: DbSession, user: AdminUser
):
    try:
        item = await OpsService(db).update_badcase(user, case_id, body)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="Bad Case 已更新")


@router.get("/metrics")
async def get_metrics(db: DbSession, user: AdminUser):
    _ = user
    summary = await OpsService(db).metrics_summary()
    return success_response(data=summary.model_dump(mode="json"))


@router.get("/audits")
async def list_audits(
    db: DbSession,
    user: AdminUser,
    operator: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    _ = user
    items = await OpsService(db).list_audits(operator=operator, action=action, limit=limit)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.get("/rbac")
async def get_rbac(db: DbSession, user: AdminUser):
    _ = db
    _ = user
    return success_response(data=OpsService(db).rbac_matrix())
