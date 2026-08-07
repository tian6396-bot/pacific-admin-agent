"""服务目录与任务仓储。"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import ServiceCatalog, Task, TaskEvent


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_enabled(self) -> list[ServiceCatalog]:
        result = await self.db.execute(
            select(ServiceCatalog)
            .where(ServiceCatalog.enabled.is_(True))
            .order_by(ServiceCatalog.priority, ServiceCatalog.name)
        )
        return list(result.scalars().all())

    async def get(self, service_id: str) -> ServiceCatalog | None:
        result = await self.db.execute(select(ServiceCatalog).where(ServiceCatalog.id == service_id))
        return result.scalar_one_or_none()

    async def create(self, item: ServiceCatalog) -> ServiceCatalog:
        self.db.add(item)
        await self.db.flush()
        return item

    async def count(self) -> int:
        result = await self.db.execute(select(ServiceCatalog.id))
        return len(result.scalars().all())


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task: Task) -> Task:
        self.db.add(task)
        await self.db.flush()
        return task

    async def add_event(self, event: TaskEvent) -> TaskEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    async def get(self, task_id: str) -> Task | None:
        result = await self.db.execute(
            select(Task).options(selectinload(Task.events)).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: str,
        tab: str | None = None,
    ) -> list[Task]:
        stmt = select(Task).options(selectinload(Task.events))
        if tab == "approve":
            stmt = stmt.where(
                Task.approver_id == user_id,
                Task.status == "pending_approve",
            )
        elif tab == "planner":
            stmt = stmt.where(Task.applicant_id == user_id, Task.kind == "planner")
        elif tab == "history":
            stmt = stmt.where(
                Task.applicant_id == user_id,
                Task.status.in_(("done", "rejected", "cancelled")),
            )
        elif tab == "active":
            stmt = stmt.where(
                Task.applicant_id == user_id,
                Task.status.in_(("pending_approve", "processing", "need_materials")),
            )
        else:
            stmt = stmt.where(
                or_(Task.applicant_id == user_id, Task.approver_id == user_id)
            )
        stmt = stmt.order_by(Task.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())
