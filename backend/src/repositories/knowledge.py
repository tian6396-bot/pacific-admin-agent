"""知识文档与 Chunk 仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import KnowledgeChunk, KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        type_: str | None = None,
        status: str | None = None,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).options(selectinload(KnowledgeDocument.chunks))
        if type_:
            stmt = stmt.where(KnowledgeDocument.type == type_)
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status)
        stmt = stmt.order_by(KnowledgeDocument.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_id(self, doc_id: str) -> KnowledgeDocument | None:
        result = await self.db.execute(
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def create(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        await self.db.flush()
        return doc

    async def delete_chunks(self, document_id: str) -> None:
        from sqlalchemy import delete

        await self.db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
        await self.db.flush()

    async def get_chunk(self, chunk_id: str) -> KnowledgeChunk | None:
        result = await self.db.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id))
        return result.scalar_one_or_none()

    async def list_published(self) -> list[KnowledgeDocument]:
        result = await self.db.execute(
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.status == "published")
        )
        return list(result.scalars().unique().all())
