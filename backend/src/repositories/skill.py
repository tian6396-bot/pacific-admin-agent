"""Skill / 工具 / 运行实例仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SkillDef, SkillRun, ToolDef


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_skills(self, status: str | None = None) -> list[SkillDef]:
        stmt = select(SkillDef).order_by(SkillDef.priority, SkillDef.id)
        if status:
            stmt = stmt.where(SkillDef.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_skill(self, skill_id: str) -> SkillDef | None:
        result = await self.db.execute(select(SkillDef).where(SkillDef.id == skill_id))
        return result.scalar_one_or_none()

    async def get_skill_by_intent(self, intent: str) -> SkillDef | None:
        result = await self.db.execute(
            select(SkillDef).where(
                SkillDef.intent == intent,
                SkillDef.status == "published",
                SkillDef.runnable.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create_skill(self, skill: SkillDef) -> SkillDef:
        self.db.add(skill)
        await self.db.flush()
        return skill

    async def count_skills(self) -> int:
        result = await self.db.execute(select(SkillDef.id))
        return len(result.scalars().all())

    async def list_tools(self) -> list[ToolDef]:
        result = await self.db.execute(select(ToolDef).order_by(ToolDef.id))
        return list(result.scalars().all())

    async def get_tool(self, tool_id: str) -> ToolDef | None:
        result = await self.db.execute(select(ToolDef).where(ToolDef.id == tool_id))
        return result.scalar_one_or_none()

    async def create_tool(self, tool: ToolDef) -> ToolDef:
        self.db.add(tool)
        await self.db.flush()
        return tool

    async def count_tools(self) -> int:
        result = await self.db.execute(select(ToolDef.id))
        return len(result.scalars().all())

    async def create_run(self, run: SkillRun) -> SkillRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def get_run(self, run_id: str) -> SkillRun | None:
        result = await self.db.execute(select(SkillRun).where(SkillRun.id == run_id))
        return result.scalar_one_or_none()

    async def get_pending_by_session(self, session_id: str, user_id: str) -> SkillRun | None:
        result = await self.db.execute(
            select(SkillRun)
            .where(
                SkillRun.session_id == session_id,
                SkillRun.user_id == user_id,
                SkillRun.status == "awaiting_confirm",
            )
            .order_by(SkillRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
