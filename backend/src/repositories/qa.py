"""质检 / 回访仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FollowupTask, QaRecord


class QaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_records(self) -> list[QaRecord]:
        result = await self.db.execute(select(QaRecord).order_by(QaRecord.created_at.desc()))
        return list(result.scalars().all())

    async def count_records(self) -> int:
        result = await self.db.execute(select(QaRecord.id))
        return len(result.scalars().all())

    async def add_record(self, row: QaRecord) -> QaRecord:
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_followups(self) -> list[FollowupTask]:
        result = await self.db.execute(
            select(FollowupTask).order_by(FollowupTask.due_date.asc())
        )
        return list(result.scalars().all())

    async def get_followup(self, fid: str) -> FollowupTask | None:
        result = await self.db.execute(select(FollowupTask).where(FollowupTask.id == fid))
        return result.scalar_one_or_none()

    async def count_followups(self) -> int:
        result = await self.db.execute(select(FollowupTask.id))
        return len(result.scalars().all())

    async def add_followup(self, row: FollowupTask) -> FollowupTask:
        self.db.add(row)
        await self.db.flush()
        return row
