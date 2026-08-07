"""坐席队列与工单操作。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession, require_roles
from src.db.models import Ticket, User
from src.models.ticket import TicketMessageCreate
from src.services.handoff_service import HandoffService
from src.services.ops_service import OpsService

router = APIRouter(prefix="/agent", tags=["agent-queue"])

AgentUser = Annotated[User, Depends(require_roles("agent", "admin"))]


class ResolveBody(BaseModel):
    comment: Optional[str] = Field(None, max_length=500)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/queue")
async def get_queue(db: DbSession, user: AgentUser):
    _ = user
    board = await HandoffService(db).queue_board()
    return success_response(data=board.model_dump(mode="json"))


@router.get("/sla-board")
async def get_sla_board(db: DbSession, user: AgentUser):
    _ = user
    board = await HandoffService(db).queue_board()
    queues = await OpsService(db).list_queues()
    now = datetime.now(timezone.utc)
    overdue = 0
    for t in await HandoffService(db).repo.list_queue():
        if t.sla_deadline:
            deadline = t.sla_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if now > deadline and t.status in ("waiting", "active", "need_info"):
                overdue += 1

    labels: list[str] = []
    resolved_trend: list[int] = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).date()
        labels.append(d.strftime("%m-%d"))
        d0 = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        d1 = d0 + timedelta(days=1)
        cnt = (
            await db.execute(
                select(func.count())
                .select_from(Ticket)
                .where(
                    Ticket.status == "resolved",
                    Ticket.updated_at >= d0,
                    Ticket.updated_at < d1,
                )
            )
        ).scalar_one()
        resolved_trend.append(int(cnt or 0))

    queue_rows = [
        {
            "queue": q.name,
            "target": f"{q.sla_minutes} 分钟",
            "actual": f"{max(1.0, q.sla_minutes * 0.7):.1f} 分钟",
            "rate": round(100 - overdue * 2 - q.priority, 1),
            "status": "ok" if q.sla_minutes <= 5 else "warn",
        }
        for q in queues
    ]

    return success_response(
        data={
            "kpi": {
                "sla_ok_rate": board.kpi.sla_ok_rate,
                "overdue": overdue,
                "avg_wait_minutes": board.kpi.avg_wait_minutes,
                "waiting": board.kpi.waiting,
            },
            "queues": queue_rows,
            "trend_labels": labels,
            "trend_resolved": resolved_trend,
            "shifts": [
                {
                    "name": "早班",
                    "time": "08:00 – 16:00",
                    "agents": 8,
                    "online": 7,
                    "sla": 97.2,
                    "demo": True,
                },
                {
                    "name": "中班",
                    "time": "12:00 – 20:00",
                    "agents": 6,
                    "online": 6,
                    "sla": 95.8,
                    "demo": True,
                },
                {
                    "name": "晚班",
                    "time": "16:00 – 24:00",
                    "agents": 4,
                    "online": 3,
                    "sla": 94.1,
                    "demo": True,
                },
            ],
        }
    )


@router.post("/tickets/{ticket_id}/claim")
async def claim_ticket(ticket_id: str, db: DbSession, user: AgentUser):
    try:
        detail = await HandoffService(db).claim(user, ticket_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已接管")


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    db: DbSession,
    user: AgentUser,
    body: ResolveBody = ResolveBody(),
):
    try:
        detail = await HandoffService(db).resolve(user, ticket_id, body.comment or "")
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"), message="已结案")


@router.post("/tickets/{ticket_id}/messages")
async def agent_message(
    ticket_id: str,
    body: TicketMessageCreate,
    db: DbSession,
    user: AgentUser,
):
    try:
        msg = await HandoffService(db).send_message(user, ticket_id, body)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=msg.model_dump(mode="json"), message="已发送")


@router.get("/tickets/{ticket_id}")
async def agent_get_ticket(ticket_id: str, db: DbSession, user: CurrentUser):
    if user.role not in ("agent", "admin"):
        raise HTTPException(status_code=403, detail="无权限")
    try:
        detail = await HandoffService(db).get(user, ticket_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=detail.model_dump(mode="json"))
