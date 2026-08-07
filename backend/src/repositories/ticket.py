"""工单仓储。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Ticket, TicketMessage


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        await self.db.flush()
        return ticket

    async def add_message(self, message: TicketMessage) -> TicketMessage:
        self.db.add(message)
        await self.db.flush()
        return message

    async def get(self, ticket_id: str) -> Ticket | None:
        result = await self.db.execute(
            select(Ticket).options(selectinload(Ticket.messages)).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def list_for_employee(self, employee_id: str) -> list[Ticket]:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.employee_id == employee_id)
            .order_by(Ticket.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_queue(self) -> list[Ticket]:
        """排队中 + 处理中（供看板）。"""
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.status.in_(("waiting", "active", "need_info", "need_expert")))
            .order_by(
                Ticket.priority.desc(),
                Ticket.created_at.asc(),
            )
        )
        return list(result.scalars().all())

    async def list_waiting(self) -> list[Ticket]:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.status == "waiting")
            .order_by(Ticket.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_waiting(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == "waiting")
        )
        return int(result.scalar_one() or 0)

    async def count_claimed_today(self) -> int:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.agent_id.is_not(None), Ticket.updated_at >= start)
        )
        return int(result.scalar_one() or 0)

    async def list_resolved_sample(self, limit: int = 50) -> list[Ticket]:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.status.in_(("resolved", "closed")))
            .order_by(Ticket.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
