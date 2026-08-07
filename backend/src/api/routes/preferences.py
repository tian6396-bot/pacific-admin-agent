"""用户偏好路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.notify import PreferenceUpdate
from src.services.notify_service import NotifyService

router = APIRouter(prefix="/users/me", tags=["preferences"])


@router.get("/preferences")
async def get_preferences(db: DbSession, user: CurrentUser):
    pref = await NotifyService(db).get_preferences(user)
    return success_response(data=pref.model_dump(mode="json"))


@router.put("/preferences")
async def put_preferences(body: PreferenceUpdate, db: DbSession, user: CurrentUser):
    try:
        pref = await NotifyService(db).update_preferences(user, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return success_response(data=pref.model_dump(mode="json"), message="偏好已保存")
