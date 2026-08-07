"""转人工：入队、交接包、接管、消息、结案。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Ticket, TicketMessage, User
from src.models.ticket import (
    HandoffPackage,
    HandoffRequest,
    QueueBoard,
    QueueKPI,
    TicketDetail,
    TicketMessageCreate,
    TicketMessagePublic,
    TicketPublic,
)
from src.repositories.chat import ChatRepository
from src.repositories.ticket import TicketRepository
from src.services.ws_hub import chat_ws_hub

logger = get_logger()

SLA_MINUTES = 5
PRIORITY_RANK = {"urgent": 3, "high": 2, "normal": 1}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_handoff(raw: str) -> HandoffPackage:
    try:
        return HandoffPackage.model_validate(json.loads(raw or "{}"))
    except Exception:  # noqa: BLE001
        return HandoffPackage()


class HandoffService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TicketRepository(db)
        self.chats = ChatRepository(db)

    async def _commit_visible(self) -> None:
        """写库后立刻提交，避免响应发出前其他请求仍读到旧状态。"""
        await self.db.commit()

    def _wait_minutes(self, ticket: Ticket) -> int:
        created = ticket.created_at or _now()
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        delta = _now() - created
        return max(0, int(delta.total_seconds() // 60))

    def _sla_overdue(self, ticket: Ticket) -> bool:
        if ticket.status not in ("waiting", "active", "need_info", "need_expert"):
            return False
        if not ticket.sla_deadline:
            return False
        deadline = ticket.sla_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        return _now() > deadline

    def to_public(self, ticket: Ticket) -> TicketPublic:
        return TicketPublic(
            id=ticket.id,
            subject=ticket.subject,
            channel=ticket.channel,
            status=ticket.status,  # type: ignore[arg-type]
            priority=ticket.priority,  # type: ignore[arg-type]
            employee_id=ticket.employee_id,
            employee_name=ticket.employee_name,
            employee_dept=ticket.employee_dept,
            agent_id=ticket.agent_id,
            agent_name=ticket.agent_name,
            chat_session_id=ticket.chat_session_id,
            wait_minutes=self._wait_minutes(ticket),
            sla_deadline=ticket.sla_deadline,
            sla_overdue=self._sla_overdue(ticket),
            handoff=_parse_handoff(ticket.handoff_json),
            created_at=ticket.created_at or _now(),
            updated_at=ticket.updated_at or _now(),
        )

    def to_detail(self, ticket: Ticket) -> TicketDetail:
        base = self.to_public(ticket)
        messages = [
            TicketMessagePublic(
                id=m.id,
                ticket_id=m.ticket_id,
                role=m.role,  # type: ignore[arg-type]
                content=m.content,
                sender_name=m.sender_name,
                created_at=m.created_at or _now(),
            )
            for m in (ticket.messages or [])
        ]
        return TicketDetail(**base.model_dump(), messages=messages)

    async def _build_handoff(
        self, user: User, session_id: str | None, reason: str
    ) -> HandoffPackage:
        evidence: list[str] = []
        summary_parts = [reason]
        intent = "human_review"
        confidence = 0.9
        if session_id:
            session = await self.chats.get_session(session_id, user.id)
            if session:
                recent = await self.chats.recent_messages(session_id, 6)
                lines = []
                for m in recent:
                    lines.append(f"{m.role}: {m.content[:120]}")
                    if m.role == "assistant" and m.citations_json:
                        try:
                            cites = json.loads(m.citations_json)
                            for c in cites[:2]:
                                title = c.get("title")
                                if title and title not in evidence:
                                    evidence.append(str(title))
                        except Exception:  # noqa: BLE001
                            pass
                    if m.route:
                        intent = m.route
                if lines:
                    summary_parts.append("最近对话：\n" + "\n".join(lines[-4:]))
        if user.department:
            evidence.append(f"员工画像：{user.department} · {user.name}")
        return HandoffPackage(
            intent=intent,
            confidence=confidence,
            summary="\n".join(summary_parts)[:1500],
            evidence=evidence,
            chat_session_id=session_id,
        )

    async def create_handoff(self, user: User, body: HandoffRequest) -> TicketDetail:
        # 避免重复排队：同一会话已有 waiting/active 则复用
        if body.session_id:
            existing_list = await self.repo.list_for_employee(user.id)
            for t in existing_list:
                if t.chat_session_id == body.session_id and t.status in (
                    "waiting",
                    "active",
                    "need_info",
                    "need_expert",
                ):
                    detail = await self.get(user, t.id)
                    return detail

        handoff = await self._build_handoff(user, body.session_id, body.reason)
        topic = (body.topic or "").strip()
        if not topic and body.session_id:
            session = await self.chats.get_session(body.session_id, user.id)
            if session:
                topic = session.title
        if not topic:
            topic = body.reason[:40] or "转人工咨询"

        ticket_id = str(uuid.uuid4())
        ticket = Ticket(
            id=ticket_id,
            subject=topic,
            channel="智能对话",
            status="waiting",
            priority=body.priority,
            employee_id=user.id,
            employee_name=user.name,
            employee_dept=user.department,
            chat_session_id=body.session_id,
            handoff_json=handoff.model_dump_json(),
            sla_deadline=_now() + timedelta(minutes=SLA_MINUTES),
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.create(ticket)
        await self.repo.add_message(
            TicketMessage(
                id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                role="system",
                content=f"已进入人工队列，预计 SLA {SLA_MINUTES} 分钟内接入。原因：{body.reason}",
                sender_name="系统",
                created_at=_now(),
            )
        )
        if handoff.summary:
            await self.repo.add_message(
                TicketMessage(
                    id=str(uuid.uuid4()),
                    ticket_id=ticket_id,
                    role="ai",
                    content=f"【交接摘要】\n{handoff.summary}",
                    sender_name="AI",
                    created_at=_now(),
                )
            )

        ticket = await self.repo.get(ticket_id)
        assert ticket is not None
        from src.services.ops_service import write_audit

        await write_audit(
            self.db,
            user,
            action="转人工",
            target=f"{ticket_id} {topic}",
        )
        await self._commit_visible()
        ticket = await self.repo.get(ticket_id)
        assert ticket is not None
        detail = self.to_detail(ticket)
        await chat_ws_hub.broadcast(
            f"ticket:{ticket_id}",
            {"type": "ticket", "event": "created", "ticket": detail.model_dump(mode="json")},
        )
        await chat_ws_hub.broadcast(
            "agent:queue",
            {"type": "queue", "event": "refresh"},
        )
        logger.info("Handoff created", ticket_id=ticket_id, employee=user.username)
        return detail

    async def list_mine(self, user: User) -> list[TicketPublic]:
        items = await self.repo.list_for_employee(user.id)
        return [self.to_public(t) for t in items]

    async def get(self, user: User, ticket_id: str) -> TicketDetail:
        ticket = await self.repo.get(ticket_id)
        if ticket is None:
            raise FileNotFoundError("工单不存在")
        if user.role == "employee" and ticket.employee_id != user.id:
            raise PermissionError("无权查看该工单")
        if user.role == "agent" and ticket.status == "waiting":
            pass  # 可查看排队详情
        elif user.role == "agent" and ticket.agent_id not in (None, user.id):
            # 其他坐席处理中仍可读（演示）
            pass
        return self.to_detail(ticket)

    async def queue_board(self) -> QueueBoard:
        items = await self.repo.list_queue()
        items_sorted = sorted(
            items,
            key=lambda t: (-PRIORITY_RANK.get(t.priority, 0), t.created_at or _now()),
        )
        waiting = [t for t in items_sorted if t.status == "waiting"]
        waits = [self._wait_minutes(t) for t in waiting] or [0]
        resolved = await self.repo.list_resolved_sample(30)
        sla_ok = 0
        for t in resolved:
            if t.sla_deadline and t.updated_at:
                deadline = t.sla_deadline
                updated = t.updated_at
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                if updated <= deadline:
                    sla_ok += 1
        total_res = len(resolved) or 1
        kpi = QueueKPI(
            waiting=await self.repo.count_waiting(),
            today_claimed=await self.repo.count_claimed_today(),
            avg_wait_minutes=round(sum(waits) / len(waits), 1),
            sla_ok_rate=round(100.0 * sla_ok / total_res, 1) if resolved else 100.0,
        )
        return QueueBoard(kpi=kpi, items=[self.to_public(t) for t in items_sorted])

    async def claim(self, agent: User, ticket_id: str) -> TicketDetail:
        if agent.role not in ("agent", "admin"):
            raise PermissionError("仅坐席可接管")
        ticket = await self.repo.get(ticket_id)
        if ticket is None:
            raise FileNotFoundError("工单不存在")
        if ticket.status != "waiting":
            raise ValueError("该工单不在排队中")

        ticket.status = "active"
        ticket.agent_id = agent.id
        ticket.agent_name = agent.name
        ticket.updated_at = _now()
        msg = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            role="system",
            content=f"坐席 {agent.name} 已接入",
            sender_name="系统",
            created_at=_now(),
        )
        await self.repo.add_message(msg)
        await self.db.flush()
        await self._commit_visible()
        ticket = await self.repo.get(ticket_id)
        assert ticket is not None
        detail = self.to_detail(ticket)
        payload = {"type": "ticket", "event": "claimed", "ticket": detail.model_dump(mode="json")}
        await chat_ws_hub.broadcast(f"ticket:{ticket_id}", payload)
        await chat_ws_hub.broadcast("agent:queue", {"type": "queue", "event": "refresh"})
        return detail

    async def send_message(
        self, user: User, ticket_id: str, body: TicketMessageCreate
    ) -> TicketMessagePublic:
        ticket = await self.repo.get(ticket_id)
        if ticket is None:
            raise FileNotFoundError("工单不存在")
        if ticket.status in ("resolved", "closed"):
            raise ValueError("工单已结束")

        if user.role == "employee":
            if ticket.employee_id != user.id:
                raise PermissionError("无权发言")
            role = "employee"
        elif user.role in ("agent", "admin"):
            if ticket.status == "waiting":
                raise ValueError("请先接管工单")
            role = "agent"
        else:
            raise PermissionError("无权发言")

        message = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            role=role,
            content=body.content.strip(),
            sender_name=user.name,
            created_at=_now(),
        )
        await self.repo.add_message(message)
        ticket.updated_at = _now()
        await self.db.flush()
        await self._commit_visible()

        public = TicketMessagePublic(
            id=message.id,
            ticket_id=message.ticket_id,
            role=message.role,  # type: ignore[arg-type]
            content=message.content,
            sender_name=message.sender_name,
            created_at=message.created_at or _now(),
        )
        await chat_ws_hub.broadcast(
            f"ticket:{ticket_id}",
            {
                "type": "message",
                "ticket_id": ticket_id,
                "message": public.model_dump(mode="json"),
            },
        )
        return public

    async def resolve(self, agent: User, ticket_id: str, comment: str = "") -> TicketDetail:
        if agent.role not in ("agent", "admin"):
            raise PermissionError("仅坐席可结案")
        ticket = await self.repo.get(ticket_id)
        if ticket is None:
            raise FileNotFoundError("工单不存在")
        if ticket.agent_id not in (None, agent.id) and agent.role != "admin":
            raise PermissionError("非本人工单")
        if ticket.status in ("resolved", "closed"):
            raise ValueError("工单已结束")

        ticket.status = "resolved"
        ticket.agent_id = ticket.agent_id or agent.id
        ticket.agent_name = ticket.agent_name or agent.name
        ticket.updated_at = _now()
        text = comment.strip() or f"坐席 {agent.name} 已办结"
        await self.repo.add_message(
            TicketMessage(
                id=str(uuid.uuid4()),
                ticket_id=ticket.id,
                role="system",
                content=text,
                sender_name="系统",
                created_at=_now(),
            )
        )
        await self.db.flush()
        await self._commit_visible()
        ticket = await self.repo.get(ticket_id)
        assert ticket is not None
        detail = self.to_detail(ticket)
        await chat_ws_hub.broadcast(
            f"ticket:{ticket_id}",
            {"type": "ticket", "event": "resolved", "ticket": detail.model_dump(mode="json")},
        )
        await chat_ws_hub.broadcast("agent:queue", {"type": "queue", "event": "refresh"})
        return detail
