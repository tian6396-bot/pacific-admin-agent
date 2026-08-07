"""站内消息路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.services.notify_service import NotifyService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(db: DbSession, user: CurrentUser):
    items = await NotifyService(db).list_for_user(user)
    unread = sum(1 for i in items if not i.read)
    return success_response(
        data={
            "items": [i.model_dump(mode="json") for i in items],
            "unread": unread,
        }
    )


@router.get("/unread-count")
async def unread_count(db: DbSession, user: CurrentUser):
    n = await NotifyService(db).unread_count(user)
    return success_response(data={"unread": n})


@router.post("/read-all")
async def mark_all_read(db: DbSession, user: CurrentUser):
    n = await NotifyService(db).mark_read(user, all_read=True)
    return success_response(data={"updated": n}, message="已全部标为已读")


@router.post("/{nid}/read")
async def mark_one_read(nid: str, db: DbSession, user: CurrentUser):
    n = await NotifyService(db).mark_read(user, nid)
    return success_response(data={"updated": n})
