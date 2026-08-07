"""质检打分与回访任务。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FollowupTask, QaRecord, User
from src.models.qa import (
    FollowupPublic,
    FollowupUpdate,
    QaItemScore,
    QaRecordCreate,
    QaRecordPublic,
)
from src.repositories.qa import QaRepository

logger = get_logger()


def _now() -> datetime:
    return datetime.now(timezone.utc)


SEED_RECORDS = (
    {
        "id": "QA-001",
        "session_label": "s-demo-001",
        "agent_name": "王敏",
        "score": 88,
        "items": [
            {"label": "响应时效", "score": 18, "max": 20},
            {"label": "问题解决", "score": 22, "max": 25},
            {"label": "服务态度", "score": 24, "max": 25},
            {"label": "流程规范", "score": 24, "max": 30},
        ],
        "reviewer": "质检 · 系统",
    },
    {
        "id": "QA-002",
        "session_label": "s-demo-002",
        "agent_name": "王敏",
        "score": 72,
        "items": [
            {"label": "响应时效", "score": 15, "max": 20},
            {"label": "问题解决", "score": 18, "max": 25},
            {"label": "服务态度", "score": 22, "max": 25},
            {"label": "流程规范", "score": 17, "max": 30},
        ],
        "reviewer": "质检 · 系统",
    },
)

SEED_FOLLOWUPS = (
    {
        "id": "FU-001",
        "employee_name": "张敏",
        "type": "满意度回访",
        "due_date": "2026-08-10",
        "status": "pending",
        "assignee": "王敏",
    },
    {
        "id": "FU-002",
        "employee_name": "张敏",
        "type": "问题解决确认",
        "due_date": "2026-08-05",
        "status": "overdue",
        "assignee": "王敏",
    },
    {
        "id": "FU-003",
        "employee_name": "张敏",
        "type": "满意度回访",
        "due_date": "2026-08-12",
        "status": "done",
        "assignee": "王敏",
    },
)


class QaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QaRepository(db)

    async def ensure_seed(self) -> None:
        if await self.repo.count_records() == 0:
            for item in SEED_RECORDS:
                await self.repo.add_record(
                    QaRecord(
                        id=item["id"],
                        ticket_id=None,
                        session_label=item["session_label"],
                        agent_name=item["agent_name"],
                        score=item["score"],
                        items_json=json.dumps(item["items"], ensure_ascii=False),
                        reviewer=item["reviewer"],
                        created_at=_now(),
                    )
                )
            logger.info("Seeded QA records", count=len(SEED_RECORDS))
        if await self.repo.count_followups() == 0:
            for item in SEED_FOLLOWUPS:
                await self.repo.add_followup(
                    FollowupTask(
                        id=item["id"],
                        employee_name=item["employee_name"],
                        type=item["type"],
                        due_date=item["due_date"],
                        status=item["status"],
                        assignee=item["assignee"],
                        created_at=_now(),
                        updated_at=_now(),
                    )
                )
            logger.info("Seeded followups", count=len(SEED_FOLLOWUPS))

    @staticmethod
    def to_record(row: QaRecord) -> QaRecordPublic:
        try:
            items_raw = json.loads(row.items_json or "[]")
        except json.JSONDecodeError:
            items_raw = []
        items = [QaItemScore(**x) for x in items_raw]
        return QaRecordPublic(
            id=row.id,
            ticket_id=row.ticket_id,
            session_label=row.session_label,
            agent_name=row.agent_name,
            score=row.score,
            items=items,
            reviewer=row.reviewer,
            created_at=row.created_at,
        )

    @staticmethod
    def to_followup(row: FollowupTask) -> FollowupPublic:
        return FollowupPublic(
            id=row.id,
            employee_name=row.employee_name,
            type=row.type,
            due_date=row.due_date,
            status=row.status,  # type: ignore[arg-type]
            assignee=row.assignee,
            ticket_id=row.ticket_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_records(self) -> list[QaRecordPublic]:
        return [self.to_record(r) for r in await self.repo.list_records()]

    async def create_record(self, user: User, body: QaRecordCreate) -> QaRecordPublic:
        score = sum(i.score for i in body.items) if body.items else 0
        row = QaRecord(
            id=str(uuid.uuid4()),
            ticket_id=body.ticket_id,
            session_label=body.session_label or "",
            agent_name=body.agent_name,
            score=score,
            items_json=json.dumps([i.model_dump() for i in body.items], ensure_ascii=False),
            reviewer=body.reviewer or user.name,
            created_at=_now(),
        )
        await self.repo.add_record(row)
        return self.to_record(row)

    async def list_followups(self) -> list[FollowupPublic]:
        return [self.to_followup(r) for r in await self.repo.list_followups()]

    async def update_followup(
        self, user: User, fid: str, body: FollowupUpdate
    ) -> FollowupPublic:
        _ = user
        row = await self.repo.get_followup(fid)
        if row is None:
            raise FileNotFoundError("回访任务不存在")
        data = body.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _now()
        await self.db.flush()
        return self.to_followup(row)
