"""知识生命周期：创建/解析/审核/发布/下线/检索。"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import BACKEND_ROOT, settings
from src.db.models import KnowledgeDocument, User
from src.models.knowledge import (
    ChunkPublic,
    ChunkUpdate,
    KnowledgeCreate,
    KnowledgeDetail,
    KnowledgePublic,
    KnowledgeUpdate,
    SearchHit,
    SearchRequest,
    SearchResponse,
)
from src.repositories.knowledge import KnowledgeRepository
from src.services.knowledge_pipeline import build_chunks, extract_text_from_pdf
from src.services.vector_index import get_vector_index

logger = get_logger()

ALLOWED_TRANSITIONS = {
    ("draft", "review"),
    ("review", "published"),
    ("draft", "published"),  # 演示可直发
    ("published", "offline"),
}

_DOMAIN_KEYWORDS = (
    "差旅",
    "住宿",
    "酒店",
    "报销",
    "年假",
    "超标",
    "深圳",
    "北京",
    "上海",
    "广州",
    "一线",
    "省会",
    "职级",
    "标准",
    "上限",
    "审批",
    "发票",
    "t3",
    "t2",
    "t1",
)

TRAVEL_FAQ_CONTENT = (
    "【差旅住宿标准】深圳、北京、上海、广州等一线城市：T3 及以下职级住宿上限 600 元/晚；"
    "T2 职级上限 800 元/晚。省会城市住宿上限 450 元/晚；其他城市住宿上限 350 元/晚。"
    "超标需事前审批，发票抬头须与公司全称一致。"
)


def _upload_root() -> Path:
    path = Path(settings.upload_dir)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _keyword_overlap(query: str, text: str) -> float:
    """中文友好的关键词重合分（0~1+），用于检索重排与兜底。"""
    q = (query or "").strip().lower()
    t = (text or "").strip().lower()
    if not q or not t:
        return 0.0
    terms: set[str] = set()
    for m in re.finditer(r"[a-z0-9]+", q):
        terms.add(m.group(0))
    for kw in _DOMAIN_KEYWORDS:
        if kw in q:
            terms.add(kw)
    # 查询中的汉字双字
    chars = re.findall(r"[\u4e00-\u9fff]", q)
    for i in range(len(chars) - 1):
        terms.add(chars[i] + chars[i + 1])
    if not terms:
        return 0.0
    hit = sum(1 for term in terms if term in t)
    return hit / max(len(terms), 1)


def _is_effective(doc: KnowledgeDocument, today: date | None = None) -> bool:
    today = today or date.today()
    if doc.effective_from and today < doc.effective_from:
        return False
    if doc.effective_to and today > doc.effective_to:
        return False
    return True


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeRepository(db)
        self.index = get_vector_index()

    def to_public(self, doc: KnowledgeDocument) -> KnowledgePublic:
        chunks = doc.chunks or []
        return KnowledgePublic(
            id=doc.id,
            title=doc.title,
            type=doc.type,  # type: ignore[arg-type]
            category=doc.category,
            status=doc.status,  # type: ignore[arg-type]
            version=doc.version,
            author=doc.author_name,
            updated_at=doc.updated_at or datetime.now(timezone.utc),
            permission_tags=doc.permission_tags,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            source_filename=doc.source_filename,
            content=doc.content,
            chunk_count=len(chunks),
            low_confidence_count=sum(1 for c in chunks if c.needs_review),
        )

    def to_detail(self, doc: KnowledgeDocument) -> KnowledgeDetail:
        base = self.to_public(doc)
        chunks = [
            ChunkPublic(
                id=c.id,
                index=c.index,
                text=c.text,
                confidence=c.confidence,
                needs_review=c.needs_review,
            )
            for c in (doc.chunks or [])
        ]
        return KnowledgeDetail(**base.model_dump(), chunks=chunks)

    async def list(self, *, type_: str | None = None, status: str | None = None) -> list[KnowledgePublic]:
        docs = await self.repo.list(type_=type_, status=status)
        return [self.to_public(d) for d in docs]

    async def get(self, doc_id: str) -> KnowledgeDetail:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise FileNotFoundError("知识不存在")
        return self.to_detail(doc)

    async def create(self, body: KnowledgeCreate, user: User) -> KnowledgeDetail:
        doc_id = str(uuid.uuid4())
        doc = KnowledgeDocument(
            id=doc_id,
            title=body.title,
            type=body.type,
            category=body.category,
            status="draft",
            version=body.version,
            author_id=user.id,
            author_name=user.name,
            permission_tags=body.permission_tags,
            effective_from=body.effective_from,
            effective_to=body.effective_to,
            content=body.content,
        )
        await self.repo.create(doc)
        chunks = build_chunks(doc_id, body.content)
        for c in chunks:
            self.db.add(c)
        await self.db.flush()
        doc = await self.repo.get_by_id(doc_id)
        assert doc is not None
        logger.info("Knowledge created", doc_id=doc_id, type=body.type)
        return self.to_detail(doc)

    async def upload_pdf(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        title: str,
        category: str,
        user: User,
        version: str = "v1",
        permission_tags: str = "全员可读",
        effective_from: date | None = None,
        effective_to: date | None = None,
    ) -> KnowledgeDetail:
        if not filename.lower().endswith(".pdf"):
            raise ValueError("仅支持 PDF 上传")

        doc_id = str(uuid.uuid4())
        dest = _upload_root() / f"{doc_id}.pdf"
        dest.write_bytes(file_bytes)

        try:
            text = extract_text_from_pdf(dest)
        except Exception:
            dest.unlink(missing_ok=True)
            raise

        doc = KnowledgeDocument(
            id=doc_id,
            title=title or Path(filename).stem,
            type="doc",
            category=category,
            status="draft",
            version=version,
            author_id=user.id,
            author_name=user.name,
            permission_tags=permission_tags,
            effective_from=effective_from,
            effective_to=effective_to,
            content=text,
            file_path=str(dest.relative_to(BACKEND_ROOT)),
            source_filename=filename,
        )
        await self.repo.create(doc)
        for c in build_chunks(doc_id, text):
            self.db.add(c)
        await self.db.flush()
        doc = await self.repo.get_by_id(doc_id)
        assert doc is not None
        return self.to_detail(doc)

    async def update(self, doc_id: str, body: KnowledgeUpdate) -> KnowledgeDetail:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise FileNotFoundError("知识不存在")
        if doc.status == "published":
            raise ValueError("已发布知识请先下线再编辑")

        data = body.model_dump(exclude_unset=True)
        content_changed = "content" in data and data["content"] is not None
        for key, value in data.items():
            setattr(doc, key, value)
        doc.updated_at = datetime.now(timezone.utc)

        if content_changed and doc.content:
            await self.repo.delete_chunks(doc_id)
            for c in build_chunks(doc_id, doc.content):
                self.db.add(c)

        await self.repo.save(doc)
        doc = await self.repo.get_by_id(doc_id)
        assert doc is not None
        return self.to_detail(doc)

    async def update_chunk(self, doc_id: str, chunk_id: str, body: ChunkUpdate) -> ChunkPublic:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise FileNotFoundError("知识不存在")
        if doc.status == "published":
            raise ValueError("已发布知识请先下线再校对")

        chunk = await self.repo.get_chunk(chunk_id)
        if chunk is None or chunk.document_id != doc_id:
            raise FileNotFoundError("Chunk 不存在")

        chunk.text = body.text.strip()
        chunk.confidence = max(chunk.confidence, 0.95)
        chunk.needs_review = False
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return ChunkPublic(
            id=chunk.id,
            index=chunk.index,
            text=chunk.text,
            confidence=chunk.confidence,
            needs_review=chunk.needs_review,
        )

    async def _transition(self, doc_id: str, target: str) -> KnowledgeDetail:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise FileNotFoundError("知识不存在")
        if (doc.status, target) not in ALLOWED_TRANSITIONS:
            raise ValueError(f"不允许从 {doc.status} 转到 {target}")

        if target == "review" and any(c.needs_review for c in (doc.chunks or [])):
            raise ValueError("仍有低置信 Chunk 未校对，请先完成校对")

        if target == "published":
            if not doc.chunks:
                raise ValueError("无 Chunk，无法发布")
            self._index_document(doc)
        if target == "offline":
            self.index.remove_document(doc.id)

        doc.status = target
        doc.updated_at = datetime.now(timezone.utc)
        await self.repo.save(doc)
        logger.info("Knowledge status changed", doc_id=doc_id, status=target)
        return self.to_detail(doc)

    def _index_document(self, doc: KnowledgeDocument) -> None:
        items = [
            (
                c.id,
                c.text,
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "version": doc.version,
                    "text": c.text,
                },
            )
            for c in (doc.chunks or [])
        ]
        self.index.remove_document(doc.id)
        self.index.upsert_chunks(items)

    async def submit(self, doc_id: str) -> KnowledgeDetail:
        return await self._transition(doc_id, "review")

    async def publish(self, doc_id: str) -> KnowledgeDetail:
        return await self._transition(doc_id, "published")

    async def offline(self, doc_id: str) -> KnowledgeDetail:
        return await self._transition(doc_id, "offline")

    async def reindex(self, doc_id: str) -> KnowledgeDetail:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise FileNotFoundError("知识不存在")
        if doc.status == "published":
            raise ValueError("已发布知识请先下线再重建索引")
        if not doc.content:
            raise ValueError("无正文可重建")

        await self.repo.delete_chunks(doc_id)
        for c in build_chunks(doc_id, doc.content):
            self.db.add(c)
        doc.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        doc = await self.repo.get_by_id(doc_id)
        assert doc is not None
        return self.to_detail(doc)

    async def search(self, body: SearchRequest) -> SearchResponse:
        hits_raw = self.index.search(body.query, top_k=body.top_k * 2)
        hits: list[SearchHit] = []
        for chunk_id, score, meta in hits_raw:
            doc_id = meta.get("document_id")
            if not doc_id:
                continue
            doc = await self.repo.get_by_id(doc_id)
            if doc is None or doc.status != "published" or not _is_effective(doc):
                continue
            text = meta.get("text") or ""
            boosted = float(score) + _keyword_overlap(body.query, f"{doc.title} {text}")
            hits.append(
                SearchHit(
                    document_id=doc.id,
                    chunk_id=chunk_id,
                    title=doc.title,
                    category=doc.category,
                    text=text,
                    score=round(boosted, 4),
                    version=doc.version,
                )
            )
            if len(hits) >= body.top_k:
                break

        best = hits[0].score if hits else 0.0
        # 向量分过低或无命中时，用关键词扫描已发布 Chunk（中文不可只靠空格切词）
        if not hits or best < 0.25:
            kw_hits = await self._keyword_search(body.query, body.top_k)
            if kw_hits:
                merged = {h.chunk_id: h for h in hits}
                for h in kw_hits:
                    prev = merged.get(h.chunk_id)
                    if prev is None or h.score > prev.score:
                        merged[h.chunk_id] = h
                hits = sorted(merged.values(), key=lambda x: x.score, reverse=True)[: body.top_k]
                return SearchResponse(hits=hits, mode="keyword-boost")

        mode = f"hybrid-{self.index.backend_name}"
        return SearchResponse(hits=hits, mode=mode)

    async def _keyword_search(self, query: str, top_k: int) -> list[SearchHit]:
        docs = await self.repo.list_published()
        scored: list[SearchHit] = []
        for doc in docs:
            if not _is_effective(doc):
                continue
            for c in doc.chunks or []:
                score = _keyword_overlap(query, f"{doc.title} {c.text}")
                if score < 0.2:
                    continue
                scored.append(
                    SearchHit(
                        document_id=doc.id,
                        chunk_id=c.id,
                        title=doc.title,
                        category=doc.category,
                        text=c.text,
                        score=round(score, 4),
                        version=doc.version,
                    )
                )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    async def sync_published_index(self) -> None:
        """启动时把库中已发布知识同步进本地向量索引。"""
        docs = await self.repo.list_published()
        for doc in docs:
            if _is_effective(doc) and doc.chunks:
                self._index_document(doc)
        logger.info("Published knowledge index synced", count=len(docs))

    async def ensure_demo_knowledge(self) -> None:
        existing = await self.repo.list()

        class _Author:
            id = "seed"
            name = "运营 · 系统"

        author = _Author()  # type: ignore[assignment]

        if not existing:
            demos = [
                KnowledgeCreate(
                    title="差旅超标如何处理？",
                    type="faq",
                    category="行政制度",
                    content=TRAVEL_FAQ_CONTENT,
                    version="v4",
                    permission_tags="全员可读",
                    effective_from=date(2025, 1, 1),
                ),
                KnowledgeCreate(
                    title="报销审批流程说明",
                    type="faq",
                    category="财务制度",
                    content=(
                        "报销需先提交申请并上传发票，直属上级审批后财务复核。"
                        "金额超过 5000 需部门负责人加签。"
                    ),
                    version="v2",
                ),
                KnowledgeCreate(
                    title="年假计算规则",
                    type="faq",
                    category="HR 制度",
                    content=(
                        "工龄满 1 年享有 5 天年假，满 10 年 10 天，满 20 年 15 天。"
                        "当年入职按在职月份折算。"
                    ),
                    version="v1",
                ),
            ]
            for item in demos:
                detail = await self.create(item, author)  # type: ignore[arg-type]
                await self.publish(detail.id)
            logger.info("Demo knowledge seeded", count=len(demos))
        else:
            # 已有库时补强差旅 FAQ，避免旧种子答不出「T3/深圳住宿」
            for doc in existing:
                if doc.title != "差旅超标如何处理？":
                    continue
                if "T3" in (doc.content or "") and "深圳" in (doc.content or ""):
                    break
                was_published = doc.status == "published"
                if was_published:
                    doc.status = "draft"
                    await self.db.flush()
                await self.update(
                    doc.id,
                    KnowledgeUpdate(content=TRAVEL_FAQ_CONTENT, version="v4"),
                )
                if was_published:
                    await self.publish(doc.id)
                logger.info("Demo travel FAQ refreshed", doc_id=doc.id)
                break

        await self.sync_published_index()
