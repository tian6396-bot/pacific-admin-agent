"""员工工单与转人工路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.ticket import HandoffRequest, TicketMessageCreate
from src.services.handoff_service import HandoffService

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("")
async def list_my_tickets(db: DbSession, user: CurrentUser):
    items = await HandoffService(db).list_mine(user)
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.post("/handoff")
async def create_handoff(body: HandoffRequest, db: DbSession, user: CurrentUser):
    try:
        detail = await HandoffService(db).create_handoff(user, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已转人工入队")


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, db: DbSession, user: CurrentUser):
    try:
        detail = await HandoffService(db).get(user, ticket_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"))


@router.post("/{ticket_id}/messages")
async def post_message(
    ticket_id: str,
    body: TicketMessageCreate,
    db: DbSession,
    user: CurrentUser,
):
    try:
        msg = await HandoffService(db).send_message(user, ticket_id, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=msg.model_dump(mode="json"), message="已发送")
