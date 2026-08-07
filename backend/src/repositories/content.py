"""内容产出仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ContentArtifact


class ContentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, row: ContentArtifact) -> ContentArtifact:
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[ContentArtifact]:
        result = await self.db.execute(
            select(ContentArtifact)
            .where(ContentArtifact.owner_id == owner_id)
            .order_by(ContentArtifact.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, artifact_id: str) -> ContentArtifact | None:
        result = await self.db.execute(
            select(ContentArtifact).where(ContentArtifact.id == artifact_id)
        )
        return result.scalar_one_or_none()
