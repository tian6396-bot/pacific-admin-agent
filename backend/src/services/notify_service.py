"""站内通知聚合与用户偏好。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Material, Notification, Task, Ticket, User, UserPreference
from src.models.notify import NotificationPublic, PreferencePublic, PreferenceUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


class NotifyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_for_user(self, user: User) -> None:
        """按任务/工单/材料生成去重通知。"""
        existing = await self.db.execute(
            select(Notification.source_key).where(Notification.user_id == user.id)
        )
        keys = set(existing.scalars().all())

        async def _ensure(
            source_key: str,
            *,
            title: str,
            preview: str,
            typ: str,
            link: str | None,
        ) -> None:
            if source_key in keys:
                return
            self.db.add(
                Notification(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    title=title,
                    preview=preview[:500],
                    type=typ,
                    link=link,
                    source_key=source_key,
                    read=False,
                    created_at=_now(),
                )
            )
            keys.add(source_key)

        tasks = (
            await self.db.execute(
                select(Task)
                .where(Task.applicant_id == user.id)
                .order_by(Task.updated_at.desc())
                .limit(20)
            )
        ).scalars().all()
        for t in tasks:
            if t.status == "need_materials":
                await _ensure(
                    f"task:materials:{t.id}",
                    title="任务提醒：待补充材料",
                    preview=f"「{t.title}」需要补充材料",
                    typ="task",
                    link=f"/tasks/{t.id}",
                )
            elif t.status == "done":
                await _ensure(
                    f"task:done:{t.id}",
                    title="任务完成",
                    preview=f"「{t.title}」已办结",
                    typ="task",
                    link=f"/tasks/{t.id}",
                )
            elif t.status == "pending_approve":
                await _ensure(
                    f"task:pending:{t.id}",
                    title="任务审批中",
                    preview=f"「{t.title}」等待审批",
                    typ="task",
                    link=f"/tasks/{t.id}",
                )

        tickets = (
            await self.db.execute(
                select(Ticket)
                .where(Ticket.employee_id == user.id)
                .order_by(Ticket.updated_at.desc())
                .limit(20)
            )
        ).scalars().all()
        for tk in tickets:
            await _ensure(
                f"ticket:{tk.status}:{tk.id}",
                title=f"工单更新：{tk.id[:8]}",
                preview=f"{tk.subject} · {tk.status}",
                typ="ticket",
                link="/tickets",
            )

        mats = (
            await self.db.execute(
                select(Material)
                .where(Material.user_id == user.id)
                .order_by(Material.updated_at.desc())
                .limit(20)
            )
        ).scalars().all()
        for m in mats:
            if m.status == "success":
                await _ensure(
                    f"material:ok:{m.id}",
                    title="材料解析成功",
                    preview=m.filename,
                    typ="material",
                    link="/materials",
                )
            elif m.status == "failed":
                await _ensure(
                    f"material:fail:{m.id}",
                    title="材料解析失败",
                    preview=m.error or m.filename,
                    typ="material",
                    link="/materials",
                )

        await self.db.flush()

    async def list_for_user(self, user: User) -> list[NotificationPublic]:
        await self.sync_for_user(user)
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        )
        rows = list(result.scalars().all())
        return [
            NotificationPublic(
                id=r.id,
                title=r.title,
                preview=r.preview,
                type=r.type,  # type: ignore[arg-type]
                read=r.read,
                link=r.link,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def mark_read(self, user: User, nid: str | None = None, *, all_read: bool = False) -> int:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user.id)
        )
        rows = list(result.scalars().all())
        n = 0
        for r in rows:
            if all_read or r.id == nid:
                if not r.read:
                    r.read = True
                    n += 1
        await self.db.flush()
        return n

    async def unread_count(self, user: User) -> int:
        await self.sync_for_user(user)
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user.id, Notification.read.is_(False)
            )
        )
        return len(result.scalars().all())

    async def get_preferences(self, user: User) -> PreferencePublic:
        row = await self.db.get(UserPreference, user.id)
        if row is None:
            row = UserPreference(user_id=user.id, updated_at=_now())
            self.db.add(row)
            await self.db.flush()
        return PreferencePublic(
            language=row.language,
            notify_task=row.notify_task,
            notify_ticket=row.notify_ticket,
            notify_system=row.notify_system,
            auto_handoff=row.auto_handoff,
            confidence_threshold=row.confidence_threshold,
        )

    async def update_preferences(self, user: User, body: PreferenceUpdate) -> PreferencePublic:
        row = await self.db.get(UserPreference, user.id)
        if row is None:
            row = UserPreference(user_id=user.id, updated_at=_now())
            self.db.add(row)
            await self.db.flush()
        data = body.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _now()
        await self.db.flush()
        return await self.get_preferences(user)
