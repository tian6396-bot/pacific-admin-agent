"""材料仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Material


class MaterialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str, *, is_admin: bool = False) -> list[Material]:
        stmt = select(Material).order_by(Material.created_at.desc())
        if not is_admin:
            stmt = stmt.where(Material.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, material_id: str) -> Material | None:
        result = await self.db.execute(select(Material).where(Material.id == material_id))
        return result.scalar_one_or_none()

    async def add(self, item: Material) -> Material:
        self.db.add(item)
        await self.db.flush()
        return item

    async def list_by_task(self, task_id: str) -> list[Material]:
        result = await self.db.execute(
            select(Material)
            .where(Material.task_id == task_id)
            .order_by(Material.created_at.desc())
        )
        return list(result.scalars().all())
