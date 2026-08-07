"""对话主链：会话 CRUD + 问答编排。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import ChatMessage, ChatSession, User
from src.models.chat import (
    ChatReply,
    Citation,
    MessagePublic,
    SendMessageRequest,
    SessionCreate,
    SessionDetail,
    SessionPublic,
)
from src.models.skill import ConfirmCard
from src.models.knowledge import SearchRequest
from src.repositories.chat import ChatRepository
from src.services import answer_generator as gen
from src.services.intent_router import route_intent
from src.services.knowledge_service import KnowledgeService
from src.services.ws_hub import chat_ws_hub

logger = get_logger()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_citations(raw: str | None) -> list[Citation]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [Citation.model_validate(item) for item in data]
    except Exception:  # noqa: BLE001
        return []


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatRepository(db)
        self.knowledge = KnowledgeService(db)

    def _session_public(self, session: ChatSession, preview: str | None = None) -> SessionPublic:
        return SessionPublic(
            id=session.id,
            title=session.title,
            created_at=session.created_at or _now(),
            updated_at=session.updated_at or _now(),
            preview=preview,
        )

    def _message_public(self, msg: ChatMessage) -> MessagePublic:
        return MessagePublic(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,  # type: ignore[arg-type]
            content=msg.content,
            citations=_parse_citations(msg.citations_json),
            route=msg.route,
            created_at=msg.created_at or _now(),
        )

    async def list_sessions(self, user: User) -> list[SessionPublic]:
        sessions = await self.repo.list_sessions(user.id)
        result: list[SessionPublic] = []
        for s in sessions:
            recent = await self.repo.recent_messages(s.id, 1)
            preview = recent[-1].content[:80] if recent else None
            result.append(self._session_public(s, preview))
        return result

    async def create_session(self, user: User, body: SessionCreate | None = None) -> SessionPublic:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=(body.title if body and body.title else "新对话"),
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.create_session(session)
        return self._session_public(session)

    async def get_session(self, user: User, session_id: str) -> SessionDetail:
        session = await self.repo.get_session(session_id, user.id)
        if session is None:
            raise FileNotFoundError("会话不存在")
        messages = [self._message_public(m) for m in (session.messages or [])]
        base = self._session_public(session)
        return SessionDetail(**base.model_dump(), messages=messages)

    async def send_message(self, user: User, body: SendMessageRequest) -> ChatReply:
        content = body.content.strip()
        if not content:
            raise ValueError("消息不能为空")

        if body.session_id:
            session = await self.repo.get_session(body.session_id, user.id)
            if session is None:
                raise FileNotFoundError("会话不存在")
        else:
            title = content[:24] + ("…" if len(content) > 24 else "")
            session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=title,
                created_at=_now(),
                updated_at=_now(),
            )
            await self.repo.create_session(session)

        await chat_ws_hub.broadcast(
            session.id,
            {"type": "status", "status": "thinking", "session_id": session.id},
        )

        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role="user",
            content=content,
            created_at=_now(),
        )
        await self.repo.add_message(user_msg)

        if session.title == "新对话":
            session.title = content[:24] + ("…" if len(content) > 24 else "")

        assistant_text, citations, route, confirm_card = await self._run_pipeline(
            session.id, content, user=user
        )

        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role="assistant",
            content=assistant_text,
            citations_json=json.dumps(
                [c.model_dump() for c in citations],
                ensure_ascii=False,
            )
            if citations
            else None,
            route=route,
            created_at=_now(),
        )
        await self.repo.add_message(assistant_msg)
        session.updated_at = _now()
        await self.db.flush()

        assistant_public = self._message_public(assistant_msg)
        assistant_public.confirm_card = confirm_card
        reply = ChatReply(
            session=self._session_public(session),
            user_message=self._message_public(user_msg),
            assistant_message=assistant_public,
            confirm_card=confirm_card,
        )

        await chat_ws_hub.broadcast(
            session.id,
            {
                "type": "message",
                "session_id": session.id,
                "message": reply.assistant_message.model_dump(mode="json"),
            },
        )
        await chat_ws_hub.broadcast(
            session.id,
            {"type": "status", "status": "done", "session_id": session.id},
        )
        logger.info("Chat replied", session_id=session.id, route=route)
        return reply

    async def _run_pipeline(
        self, session_id: str, query: str, user: User | None = None
    ) -> tuple[str, list[Citation], str, ConfirmCard | None]:
        # 短窗记忆（当前主要用于日志/后续改写扩展）
        recent = await self.repo.recent_messages(session_id, settings.short_memory_turns * 2)
        _ = recent

        # 1) 先检索，高分可直出
        search = await self.knowledge.search(SearchRequest(query=query, top_k=5))
        hits = search.hits
        best = hits[0].score if hits else 0.0
        if hits and best >= settings.qa_similarity_threshold:
            text, cites = await gen.generate_answer(query, hits[:3])
            return text, cites, "qa_direct", None

        intent = route_intent(query)

        if intent.route == "human_review":
            if user is not None:
                from src.models.ticket import HandoffRequest
                from src.services.handoff_service import HandoffService

                ticket = await HandoffService(self.db).create_handoff(
                    user,
                    HandoffRequest(
                        session_id=session_id,
                        reason=query.strip() or "用户申请转人工",
                        priority="high",
                    ),
                )
                text = (
                    f"已为您创建人工工单（{ticket.id[:8]}…），当前状态：排队中。"
                    f"预计 SLA 内坐席接入。可在「我的工单」查看进度。"
                )
                return text, [], "human_review", None
            return gen.human_placeholder(), [], "human_review", None
        if intent.route == "web":
            return gen.web_disabled_reply(), [], "web", None
        if intent.route == "skill":
            if user is not None:
                from src.services.skill_service import SkillService

                try:
                    text, card = await SkillService(self.db).start_from_intent(
                        user,
                        session_id=session_id,
                        intent=intent.intent,
                        query=query,
                    )
                    return text, [], "skill", card
                except ValueError:
                    return gen.skill_placeholder(intent.intent), [], "skill", None
            return gen.skill_placeholder(intent.intent), [], "skill", None
        if intent.route == "clarify" or intent.need_clarify:
            return await gen.conversational_reply(query, intent.reason), [], "clarify", None

        # qa_rag / fallback（关键词增强后分数多为 0.2~1.x）
        if not hits or best < 0.2:
            return await gen.conversational_reply(query, "未检索到可靠来源"), [], "fallback", None

        text, cites = await gen.generate_answer(query, hits[:3])
        return text, cites, "qa_rag", None
