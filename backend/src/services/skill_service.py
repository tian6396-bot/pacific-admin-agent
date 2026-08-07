"""Skill 状态机 + ConfirmGate。"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SkillDef, SkillRun, ToolDef, User
from src.models.catalog import TaskApplyRequest
from src.models.skill import (
    ConfirmCard,
    FlowNodePublic,
    SkillPublic,
    SkillRunPublic,
    ToolPublic,
)
from src.repositories.skill import SkillRepository
from src.services.task_service import TaskService
from src.services.tool_gateway import ToolGateway

logger = get_logger()

INTENT_TO_SKILL = {
    "leave_apply": "SK-HR-01",
    "expense_apply": "SK-FIN-02",
    "it_repair": "SK-IT-01",
    "meeting_book": "SK-ADM-01",
}

SEED_TOOLS = (
    {
        "id": "TOOL-LEAVE-CREATE",
        "name": "请假单创建",
        "method": "POST",
        "endpoint": "/hr/leave/create",
        "timeout_ms": 5000,
        "retries": 1,
        "status": "active",
        "mock_enabled": True,
        "schema_json": '{"name":"create_leave","required":["days","reason"]}',
        "mock_response": json.dumps(
            {
                "code": 0,
                "mock": True,
                "data": {"leaveId": "LV-MOCK-001", "status": "submitted"},
                "message": "请假单已提交（Mock）",
            },
            ensure_ascii=False,
        ),
    },
    {
        "id": "TOOL-EXPENSE-CREATE",
        "name": "报销草稿创建",
        "method": "POST",
        "endpoint": "/finance/expense/draft",
        "timeout_ms": 5000,
        "retries": 2,
        "status": "active",
        "mock_enabled": True,
        "schema_json": '{"name":"create_expense","required":["amount","reason"]}',
        "mock_response": json.dumps(
            {
                "code": 0,
                "mock": True,
                "data": {"expenseId": "EX-MOCK-001", "status": "draft"},
                "message": "报销草稿已创建（Mock）",
            },
            ensure_ascii=False,
        ),
    },
    {
        "id": "TOOL-IT-TICKET",
        "name": "IT 报修建单",
        "method": "POST",
        "endpoint": "/it/ticket/create",
        "timeout_ms": 8000,
        "retries": 2,
        "status": "active",
        "mock_enabled": True,
        "schema_json": '{"name":"create_it_ticket","required":["symptom"]}',
        "mock_response": json.dumps(
            {
                "code": 0,
                "mock": True,
                "data": {"ticketId": "IT-MOCK-001", "status": "open"},
                "message": "报修单已创建（Mock）",
            },
            ensure_ascii=False,
        ),
    },
    {
        "id": "TOOL-MEETING-BOOK",
        "name": "会议室预订",
        "method": "POST",
        "endpoint": "/admin/meeting/book",
        "timeout_ms": 5000,
        "retries": 1,
        "status": "active",
        "mock_enabled": True,
        "schema_json": '{"name":"book_meeting","required":["room","slot"]}',
        "mock_response": json.dumps(
            {
                "code": 0,
                "mock": True,
                "data": {"bookingId": "MT-MOCK-001", "status": "booked"},
                "message": "会议室已预订（Mock）",
            },
            ensure_ascii=False,
        ),
    },
    {
        "id": "TOOL-OA-APPROVAL",
        "name": "OA 审批创建",
        "method": "POST",
        "endpoint": "/oa/approval/create",
        "timeout_ms": 5000,
        "retries": 2,
        "status": "active",
        "mock_enabled": True,
        "schema_json": '{"name":"create_approval"}',
        "mock_response": json.dumps(
            {"code": 0, "mock": True, "data": {"approvalId": "APR-MOCK-001"}},
            ensure_ascii=False,
        ),
    },
)

DEFAULT_NODES = [
    {"id": "n1", "type": "collect", "label": "收集槽位", "config": "补齐关键字段"},
    {"id": "n2", "type": "confirm", "label": "确认卡片", "config": "写前闸，用户确认后继续"},
    {"id": "n3", "type": "invoke", "label": "调用工具", "config": "仅已登记工具 · 默认可 Mock"},
    {"id": "n4", "type": "compensate", "label": "失败补偿", "config": "提示转人工或重试"},
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(raw: str | None, default: Any) -> Any:
    try:
        return json.loads(raw or "")
    except Exception:  # noqa: BLE001
        return default


class SkillService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SkillRepository(db)
        self.gateway = ToolGateway()

    def to_skill_public(self, s: SkillDef) -> SkillPublic:
        return SkillPublic(
            id=s.id,
            name=s.name,
            intent=s.intent,
            domain=s.domain,
            status=s.status,  # type: ignore[arg-type]
            description=s.description,
            tool_id=s.tool_id,
            service_id=s.service_id,
            priority=s.priority,
        )

    def to_tool_public(self, t: ToolDef) -> ToolPublic:
        return ToolPublic(
            id=t.id,
            name=t.name,
            method=t.method,
            endpoint=t.endpoint,
            timeout_ms=t.timeout_ms,
            retries=t.retries,
            status=t.status,  # type: ignore[arg-type]
            mock_enabled=t.mock_enabled,
            schema_json=t.schema_json,
            mock_response=t.mock_response,
        )

    def nodes_of(self, skill: SkillDef) -> list[FlowNodePublic]:
        raw = _parse_json(skill.nodes_json, DEFAULT_NODES)
        return [FlowNodePublic.model_validate(n) for n in raw]

    def _confirm_card(self, run: SkillRun, skill: SkillDef, tool: ToolDef | None) -> ConfirmCard:
        return ConfirmCard(
            run_id=run.id,
            skill_id=skill.id,
            skill_name=skill.name,
            summary=run.confirm_summary,
            slots=_parse_json(run.slots_json, {}),
            mock_tool=bool(tool.mock_enabled) if tool else True,
            tool_name=tool.name if tool else None,
        )

    def to_run_public(self, run: SkillRun, skill: SkillDef | None = None) -> SkillRunPublic:
        # skill may be passed to avoid extra query in hot path
        return SkillRunPublic(
            id=run.id,
            skill_id=run.skill_id,
            skill_name=skill.name if skill else run.skill_id,
            status=run.status,  # type: ignore[arg-type]
            slots=_parse_json(run.slots_json, {}),
            confirm_summary=run.confirm_summary,
            task_id=run.task_id,
            tool_result=_parse_json(run.tool_result_json, None),
            session_id=run.session_id,
            created_at=run.created_at or _now(),
            updated_at=run.updated_at or _now(),
            confirm_card=None,
        )

    async def list_skills(self) -> list[SkillPublic]:
        return [self.to_skill_public(s) for s in await self.repo.list_skills()]

    async def list_tools(self) -> list[ToolPublic]:
        return [self.to_tool_public(t) for t in await self.repo.list_tools()]

    async def get_skill_detail(self, skill_id: str) -> tuple[SkillPublic, list[FlowNodePublic]]:
        skill = await self.repo.get_skill(skill_id)
        if skill is None:
            raise FileNotFoundError("Skill 不存在")
        return self.to_skill_public(skill), self.nodes_of(skill)

    def _extract_slots(self, intent: str, query: str) -> dict[str, Any]:
        slots: dict[str, Any] = {"raw_query": query}
        days = re.search(r"(\d+)\s*天", query)
        amount = re.search(r"(\d+(?:\.\d+)?)\s*元", query)
        if intent == "leave_apply":
            slots["days"] = days.group(1) if days else "3"
            slots["leave_type"] = "年假"
            slots["reason"] = query
        elif intent == "expense_apply":
            slots["amount"] = amount.group(1) if amount else "1000"
            slots["reason"] = query
            slots["category"] = "差旅交通"
        elif intent == "it_repair":
            slots["symptom"] = query
            slots["urgency"] = "normal"
        elif intent == "meeting_book":
            slots["room"] = "A-301"
            slots["slot"] = "明天 14:00-15:00"
            slots["reason"] = query
        return slots

    def _summary(self, skill: SkillDef, slots: dict[str, Any]) -> str:
        parts = [f"即将执行 Skill「{skill.name}」并调用工具（默认 Mock）。"]
        for k, v in slots.items():
            if k == "raw_query":
                continue
            parts.append(f"- {k}: {v}")
        parts.append("请确认后继续；取消则不会产生写操作。")
        return "\n".join(parts)

    async def start_from_intent(
        self, user: User, *, session_id: str, intent: str, query: str
    ) -> tuple[str, ConfirmCard]:
        skill_id = INTENT_TO_SKILL.get(intent)
        if not skill_id:
            raise ValueError("未找到可运行的 Skill")
        skill = await self.repo.get_skill(skill_id)
        if skill is None or skill.status != "published" or not skill.runnable:
            raise ValueError("Skill 未发布或不可运行")

        # 同会话已有待确认则复用
        pending = await self.repo.get_pending_by_session(session_id, user.id)
        if pending and pending.skill_id == skill.id:
            tool = await self.repo.get_tool(skill.tool_id) if skill.tool_id else None
            card = self._confirm_card(pending, skill, tool)
            return (
                f"已为您准备确认卡片（{skill.name}）。请确认后调用工具，或取消。",
                card,
            )

        slots = self._extract_slots(intent, query)
        run = SkillRun(
            id=str(uuid.uuid4()),
            skill_id=skill.id,
            user_id=user.id,
            session_id=session_id,
            status="awaiting_confirm",
            slots_json=json.dumps(slots, ensure_ascii=False),
            confirm_summary=self._summary(skill, slots),
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.create_run(run)
        tool = await self.repo.get_tool(skill.tool_id) if skill.tool_id else None
        card = self._confirm_card(run, skill, tool)
        logger.info("Skill run awaiting confirm", run_id=run.id, skill=skill.id)
        return (
            f"已识别办理意图，请确认下方卡片后继续（Skill：{skill.name}）。",
            card,
        )

    async def confirm(self, user: User, run_id: str) -> SkillRunPublic:
        run = await self.repo.get_run(run_id)
        if run is None:
            raise FileNotFoundError("运行实例不存在")
        if run.user_id != user.id:
            raise PermissionError("无权确认该 Skill")
        if run.status != "awaiting_confirm":
            raise ValueError(f"当前状态不可确认：{run.status}")

        skill = await self.repo.get_skill(run.skill_id)
        if skill is None:
            raise FileNotFoundError("Skill 不存在")

        # ConfirmGate：仅确认后进入 running 并调工具
        run.status = "running"
        run.updated_at = _now()
        await self.db.flush()

        tool = await self.repo.get_tool(skill.tool_id) if skill.tool_id else None
        slots = _parse_json(run.slots_json, {})
        tool_result: dict[str, Any] = {"skipped": True}
        if tool:
            tool_result = await self.gateway.invoke(
                tool,
                payload=slots,
                idempotency_key=run.id,
            )
            run.tool_result_json = json.dumps(tool_result, ensure_ascii=False)

        # 联动任务
        if skill.service_id:
            title = f"{skill.name} · {slots.get('reason') or slots.get('symptom') or '对话确认办理'}"
            title = str(title)[:200]
            task = await TaskService(self.db).apply(
                user,
                TaskApplyRequest(
                    service_id=skill.service_id,
                    title=title,
                    form=slots,
                ),
            )
            run.task_id = task.id

        run.status = "done"
        run.updated_at = _now()
        await self.db.flush()
        from src.services.ops_service import write_audit

        await write_audit(
            self.db,
            user,
            action="Skill 确认执行",
            target=f"{run.skill_id} run={run.id}",
        )
        public = self.to_run_public(run, skill)
        public.tool_result = tool_result
        logger.info("Skill confirmed and done", run_id=run.id, task_id=run.task_id)
        return public

    async def cancel(self, user: User, run_id: str, reason: str = "") -> SkillRunPublic:
        run = await self.repo.get_run(run_id)
        if run is None:
            raise FileNotFoundError("运行实例不存在")
        if run.user_id != user.id:
            raise PermissionError("无权取消")
        if run.status != "awaiting_confirm":
            raise ValueError("当前状态不可取消")
        run.status = "cancelled"
        run.updated_at = _now()
        if reason:
            run.confirm_summary = f"{run.confirm_summary}\n[已取消] {reason}"
        await self.db.flush()
        skill = await self.repo.get_skill(run.skill_id)
        return self.to_run_public(run, skill)

    async def get_run(self, user: User, run_id: str) -> SkillRunPublic:
        run = await self.repo.get_run(run_id)
        if run is None:
            raise FileNotFoundError("运行实例不存在")
        if run.user_id != user.id and user.role != "admin":
            raise PermissionError("无权查看")
        skill = await self.repo.get_skill(run.skill_id)
        public = self.to_run_public(run, skill)
        if run.status == "awaiting_confirm" and skill:
            tool = await self.repo.get_tool(skill.tool_id) if skill.tool_id else None
            public.confirm_card = self._confirm_card(run, skill, tool)
        return public

    async def ensure_seed(self) -> None:
        if await self.repo.count_tools() == 0:
            for raw in SEED_TOOLS:
                await self.repo.create_tool(ToolDef(**raw))
            logger.info("Tools seeded", count=len(SEED_TOOLS))

        if await self.repo.count_skills() > 0:
            return

        skills = [
            SkillDef(
                id="SK-FIN-01",
                name="报销材料预检",
                intent="expense_precheck",
                domain="expense",
                status="published",
                description="材料预检",
                tool_id="TOOL-EXPENSE-CREATE",
                service_id="expense",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=False,
            ),
            SkillDef(
                id="SK-FIN-02",
                name="报销草稿与补充材料",
                intent="expense_apply",
                domain="expense",
                status="published",
                description="报销办理确认后建任务",
                tool_id="TOOL-EXPENSE-CREATE",
                service_id="expense",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=True,
            ),
            SkillDef(
                id="SK-HR-01",
                name="请假申请与撤销",
                intent="leave_apply",
                domain="hr",
                status="published",
                description="请假确认办理",
                tool_id="TOOL-LEAVE-CREATE",
                service_id="leave",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=True,
            ),
            SkillDef(
                id="SK-ADM-01",
                name="会议室预订与变更",
                intent="meeting_book",
                domain="admin",
                status="published",
                description="会议室预订",
                tool_id="TOOL-MEETING-BOOK",
                service_id="meeting",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=True,
            ),
            SkillDef(
                id="SK-IT-01",
                name="IT 故障报修",
                intent="it_repair",
                domain="it",
                status="published",
                description="IT 报修建单",
                tool_id="TOOL-IT-TICKET",
                service_id="repair",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=True,
            ),
            SkillDef(
                id="SK-SVC-01",
                name="转人工与建单",
                intent="handoff",
                domain="desk",
                status="published",
                description="由 B5 交接服务承接",
                tool_id=None,
                service_id="handoff",
                priority="P0",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=False,
            ),
            SkillDef(
                id="SK-TRV-01",
                name="差旅预订",
                intent="travel_book",
                domain="travel",
                status="draft",
                description="P1 占位",
                tool_id="TOOL-OA-APPROVAL",
                service_id=None,
                priority="P1",
                nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                runnable=False,
            ),
        ]
        for s in skills:
            await self.repo.create_skill(s)
        # 再补若干只读展示用
        for sid, name, intent in (
            ("SK-TRV-02", "行程变更与取消", "travel_change"),
            ("SK-ADM-02", "访客预约", "visitor"),
            ("SK-ADM-03", "办公用品申领", "supplies"),
            ("SK-IT-02", "账号权限申请", "account_perm"),
            ("SK-AST-01", "资产领用/调拨/归还", "asset"),
            ("SK-PRC-01", "采购申请", "procurement"),
        ):
            await self.repo.create_skill(
                SkillDef(
                    id=sid,
                    name=name,
                    intent=intent,
                    domain="general",
                    status="draft",
                    description="清单可见，运行未启用",
                    priority="P1",
                    nodes_json=json.dumps(DEFAULT_NODES, ensure_ascii=False),
                    runnable=False,
                )
            )
        logger.info("Skills seeded", count=13)
