"""运营配置 / Bad Case / 审计仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AuditLog, BadCase, IntentDef, QueueSlaConfig


class OpsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Intent ---
    async def list_intents(self) -> list[IntentDef]:
        result = await self.db.execute(select(IntentDef).order_by(IntentDef.id))
        return list(result.scalars().all())

    async def get_intent(self, intent_id: str) -> IntentDef | None:
        result = await self.db.execute(select(IntentDef).where(IntentDef.id == intent_id))
        return result.scalar_one_or_none()

    async def count_intents(self) -> int:
        result = await self.db.execute(select(IntentDef.id))
        return len(result.scalars().all())

    async def add_intent(self, item: IntentDef) -> IntentDef:
        self.db.add(item)
        await self.db.flush()
        return item

    # --- Queue SLA ---
    async def list_queues(self) -> list[QueueSlaConfig]:
        result = await self.db.execute(
            select(QueueSlaConfig).order_by(QueueSlaConfig.priority, QueueSlaConfig.id)
        )
        return list(result.scalars().all())

    async def get_queue(self, queue_id: str) -> QueueSlaConfig | None:
        result = await self.db.execute(
            select(QueueSlaConfig).where(QueueSlaConfig.id == queue_id)
        )
        return result.scalar_one_or_none()

    async def count_queues(self) -> int:
        result = await self.db.execute(select(QueueSlaConfig.id))
        return len(result.scalars().all())

    async def add_queue(self, item: QueueSlaConfig) -> QueueSlaConfig:
        self.db.add(item)
        await self.db.flush()
        return item

    # --- Bad Case ---
    async def list_badcases(
        self,
        *,
        domain: str | None = None,
        status: str | None = None,
    ) -> list[BadCase]:
        stmt = select(BadCase).order_by(BadCase.created_at.desc())
        if domain and domain != "全部":
            stmt = stmt.where(BadCase.domain == domain)
        if status:
            stmt = stmt.where(BadCase.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_badcase(self, case_id: str) -> BadCase | None:
        result = await self.db.execute(select(BadCase).where(BadCase.id == case_id))
        return result.scalar_one_or_none()

    async def count_badcases(self, *, status: str | None = None) -> int:
        stmt = select(BadCase.id)
        if status:
            stmt = stmt.where(BadCase.status == status)
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def add_badcase(self, item: BadCase) -> BadCase:
        self.db.add(item)
        await self.db.flush()
        return item

    # --- Audit ---
    async def add_audit(self, item: AuditLog) -> AuditLog:
        self.db.add(item)
        await self.db.flush()
        return item

    async def list_audits(
        self,
        *,
        operator: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if operator:
            stmt = stmt.where(AuditLog.operator.contains(operator))
        if action:
            stmt = stmt.where(AuditLog.action.contains(action))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_audits(self) -> int:
        result = await self.db.execute(select(AuditLog.id))
        return len(result.scalars().all())
