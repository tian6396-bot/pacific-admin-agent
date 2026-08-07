"""对话 REST 路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.chat import SendMessageRequest, SessionCreate
from src.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/sessions")
async def list_sessions(db: DbSession, user: CurrentUser):
    items = await ChatService(db).list_sessions(user)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("/sessions")
async def create_session(db: DbSession, user: CurrentUser, body: SessionCreate = SessionCreate()):
    session = await ChatService(db).create_session(user, body)
    return success_response(data=session.model_dump(mode="json"), message="会话已创建")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: DbSession, user: CurrentUser):
    try:
        detail = await ChatService(db).get_session(user, session_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"))


@router.post("/messages")
async def send_message(body: SendMessageRequest, db: DbSession, user: CurrentUser):
    try:
        reply = await ChatService(db).send_message(user, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=reply.model_dump(mode="json"), message="已回复")
