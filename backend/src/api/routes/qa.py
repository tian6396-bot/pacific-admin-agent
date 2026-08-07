"""质检与回访路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import DbSession, require_roles
from src.db.models import User
from src.models.qa import FollowupUpdate, QaRecordCreate
from src.services.qa_service import QaService

router = APIRouter(prefix="/qa", tags=["qa"])
AgentUser = Annotated[User, Depends(require_roles("agent", "admin"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/records")
async def list_qa_records(db: DbSession, user: AgentUser):
    _ = user
    items = await QaService(db).list_records()
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("/records")
async def create_qa_record(body: QaRecordCreate, db: DbSession, user: AgentUser):
    try:
        item = await QaService(db).create_record(user, body)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="质检已登记")


@router.get("/followups")
async def list_followups(db: DbSession, user: AgentUser):
    _ = user
    items = await QaService(db).list_followups()
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.patch("/followups/{followup_id}")
async def update_followup(
    followup_id: str, body: FollowupUpdate, db: DbSession, user: AgentUser
):
    try:
        item = await QaService(db).update_followup(user, followup_id, body)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=item.model_dump(mode="json"), message="回访已更新")
