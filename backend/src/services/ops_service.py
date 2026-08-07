"""运营配置、Bad Case、指标聚合与审计。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pycore.core import get_logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    AuditLog,
    BadCase,
    ChatSession,
    IntentDef,
    KnowledgeDocument,
    QueueSlaConfig,
    Task,
    Ticket,
    User,
)
from src.models.ops import (
    AuditLogPublic,
    BadCaseCreate,
    BadCasePublic,
    BadCaseUpdate,
    IntentPublic,
    IntentUpdate,
    MetricsSummary,
    QueueSlaPublic,
    QueueSlaUpdate,
)
from src.repositories.ops import OpsRepository

logger = get_logger()

ROLE_LABEL = {"employee": "员工", "agent": "坐席", "admin": "运营管理员"}

SEED_INTENTS = (
    {
        "id": "INT-TRAVEL-OVER",
        "name": "差旅超标咨询",
        "domain": "行政",
        "slots": "超标金额, 领导姓名",
        "status": "published",
        "prompt_version": "v2.1",
        "prompt_content": (
            "你是太平洋金科的行政咨询助手。当用户咨询差旅超标问题时：\n"
            "1. 确认超标类型（机票/酒店/其他）\n"
            "2. 引用《差旅管理制度》说明审批流程\n"
            "3. 如需发起审批，收集领导姓名并确认\n"
            "4. 置信度低于 0.7 时建议转人工"
        ),
        "hit_rate": 87.3,
    },
    {
        "id": "INT-EXPENSE-QUERY",
        "name": "报销进度查询",
        "domain": "财务",
        "slots": "报销单号",
        "status": "published",
        "prompt_version": "v1.5",
        "prompt_content": "识别报销进度查询意图，引导用户提供报销单号并返回状态说明。",
        "hit_rate": 92.1,
    },
    {
        "id": "INT-LEAVE-BALANCE",
        "name": "年假余额查询",
        "domain": "HR",
        "slots": "—",
        "status": "published",
        "prompt_version": "v1.0",
        "prompt_content": "查询年假余额；无法对接 HR 系统时说明为演示数据并引导转人工。",
        "hit_rate": 95.6,
    },
    {
        "id": "INT-VPN-REPAIR",
        "name": "VPN 故障报修",
        "domain": "IT",
        "slots": "故障描述, 设备型号",
        "status": "draft",
        "prompt_version": "v0.3",
        "prompt_content": "收集 VPN 故障现象与设备信息，必要时引导发起 IT 报修 Skill。",
        "hit_rate": 0.0,
    },
)

SEED_QUEUES = (
    {
        "id": "Q-001",
        "name": "通用咨询",
        "skill_group": "综合",
        "agents": 8,
        "sla_minutes": 5,
        "priority": 1,
        "max_wait": 10,
        "alert_threshold": 80,
        "status": "active",
    },
    {
        "id": "Q-002",
        "name": "财务咨询",
        "skill_group": "财务",
        "agents": 4,
        "sla_minutes": 5,
        "priority": 2,
        "max_wait": 10,
        "alert_threshold": 80,
        "status": "active",
    },
    {
        "id": "Q-003",
        "name": "IT 支持",
        "skill_group": "IT",
        "agents": 3,
        "sla_minutes": 3,
        "priority": 3,
        "max_wait": 8,
        "alert_threshold": 75,
        "status": "active",
    },
    {
        "id": "Q-004",
        "name": "HR 咨询",
        "skill_group": "HR",
        "agents": 3,
        "sla_minutes": 5,
        "priority": 2,
        "max_wait": 10,
        "alert_threshold": 80,
        "status": "active",
    },
)

SEED_BADCASES = (
    {
        "id": "BC-001",
        "title": "差旅超标误路由至 IT 队列",
        "category": "intent",
        "domain": "行政",
        "intent": "差旅超标咨询",
        "severity": "high",
        "status": "open",
        "description": "员工咨询出差机票超标处理，系统错误路由至 IT 支持队列。",
        "root_cause": "意图识别置信度偏低且未触发澄清；队列规则未覆盖「超标+差旅」。",
        "suggestion": "优化差旅超标 Prompt；队列增加行政域兜底。",
        "session_id": None,
    },
    {
        "id": "BC-002",
        "title": "报销进度返回过期数据",
        "category": "tool",
        "domain": "财务",
        "intent": "报销进度查询",
        "severity": "medium",
        "status": "improved",
        "description": "查询报销单进度返回「审批中」但实际已通过。",
        "root_cause": "工具 Mock 数据未更新。",
        "suggestion": "缩短缓存 TTL；同步测试环境 Mock。",
        "session_id": None,
    },
)


async def write_audit(
    db: AsyncSession,
    user: User | None,
    *,
    action: str,
    target: str,
    result: str = "success",
    ip: str = "127.0.0.1",
    operator: str | None = None,
    role: str | None = None,
) -> AuditLog:
    """供各写路径调用的审计埋点（只追加）。"""
    log = AuditLog(
        id=str(uuid.uuid4()),
        operator=operator or (user.username if user else "system"),
        role=role or (user.role if user else "system"),
        action=action,
        target=target[:255],
        ip=ip,
        result=result,
        created_at=_now(),
    )
    db.add(log)
    await db.flush()
    logger.info("Audit logged", action=action, target=target, operator=log.operator)
    return log


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OpsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OpsRepository(db)

    async def ensure_seed(self) -> None:
        if await self.repo.count_intents() == 0:
            for item in SEED_INTENTS:
                await self.repo.add_intent(IntentDef(**item, updated_at=_now()))
            logger.info("Seeded intent defs", count=len(SEED_INTENTS))

        if await self.repo.count_queues() == 0:
            for item in SEED_QUEUES:
                await self.repo.add_queue(QueueSlaConfig(**item, updated_at=_now()))
            logger.info("Seeded queue SLA", count=len(SEED_QUEUES))

        if await self.repo.count_badcases() == 0:
            for item in SEED_BADCASES:
                await self.repo.add_badcase(
                    BadCase(**item, created_at=_now(), updated_at=_now())
                )
            logger.info("Seeded bad cases", count=len(SEED_BADCASES))

        if await self.repo.count_audits() == 0:
            await write_audit(
                self.db,
                None,
                action="系统初始化",
                target="运营种子数据",
                operator="system",
                role="system",
            )

    # --- mappers ---
    @staticmethod
    def to_intent(row: IntentDef) -> IntentPublic:
        return IntentPublic(
            id=row.id,
            name=row.name,
            domain=row.domain,
            slots=row.slots,
            status=row.status,  # type: ignore[arg-type]
            prompt_version=row.prompt_version,
            prompt_content=row.prompt_content,
            hit_rate=row.hit_rate,
        )

    @staticmethod
    def to_queue(row: QueueSlaConfig) -> QueueSlaPublic:
        return QueueSlaPublic(
            id=row.id,
            name=row.name,
            skill_group=row.skill_group,
            agents=row.agents,
            sla_minutes=row.sla_minutes,
            priority=row.priority,
            max_wait=row.max_wait,
            alert_threshold=row.alert_threshold,
            status=row.status,  # type: ignore[arg-type]
        )

    @staticmethod
    def to_badcase(row: BadCase) -> BadCasePublic:
        return BadCasePublic(
            id=row.id,
            title=row.title,
            category=row.category,  # type: ignore[arg-type]
            domain=row.domain,
            intent=row.intent,
            severity=row.severity,  # type: ignore[arg-type]
            status=row.status,  # type: ignore[arg-type]
            description=row.description,
            root_cause=row.root_cause,
            suggestion=row.suggestion,
            session_id=row.session_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def to_audit(row: AuditLog) -> AuditLogPublic:
        return AuditLogPublic(
            id=row.id,
            operator=row.operator,
            role=row.role,
            action=row.action,
            target=row.target,
            ip=row.ip,
            result=row.result,  # type: ignore[arg-type]
            created_at=row.created_at,
        )

    # --- intents ---
    async def list_intents(self) -> list[IntentPublic]:
        return [self.to_intent(i) for i in await self.repo.list_intents()]

    async def update_intent(
        self, user: User, intent_id: str, body: IntentUpdate
    ) -> IntentPublic:
        row = await self.repo.get_intent(intent_id)
        if row is None:
            raise FileNotFoundError("意图不存在")
        data = body.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _now()
        await self.db.flush()
        await write_audit(self.db, user, action="更新意图", target=f"{row.id} {row.name}")
        return self.to_intent(row)

    async def publish_intent(self, user: User, intent_id: str) -> IntentPublic:
        row = await self.repo.get_intent(intent_id)
        if row is None:
            raise FileNotFoundError("意图不存在")
        if not (row.prompt_content or "").strip():
            raise ValueError("Prompt 内容为空，无法发布")
        row.status = "published"
        row.updated_at = _now()
        await self.db.flush()
        await write_audit(
            self.db,
            user,
            action="发布意图",
            target=f"{row.id} {row.prompt_version}",
        )
        return self.to_intent(row)

    async def offline_intent(self, user: User, intent_id: str) -> IntentPublic:
        row = await self.repo.get_intent(intent_id)
        if row is None:
            raise FileNotFoundError("意图不存在")
        row.status = "offline"
        row.updated_at = _now()
        await self.db.flush()
        await write_audit(self.db, user, action="下线意图", target=f"{row.id} {row.name}")
        return self.to_intent(row)

    # --- queues ---
    async def list_queues(self) -> list[QueueSlaPublic]:
        return [self.to_queue(q) for q in await self.repo.list_queues()]

    async def update_queue(
        self, user: User, queue_id: str, body: QueueSlaUpdate
    ) -> QueueSlaPublic:
        row = await self.repo.get_queue(queue_id)
        if row is None:
            raise FileNotFoundError("队列不存在")
        data = body.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _now()
        await self.db.flush()
        await write_audit(
            self.db,
            user,
            action="修改 SLA",
            target=f"{row.id} {row.name} · {row.sla_minutes} 分钟",
        )
        return self.to_queue(row)

    # --- bad cases ---
    async def list_badcases(
        self, *, domain: str | None = None, status: str | None = None
    ) -> list[BadCasePublic]:
        rows = await self.repo.list_badcases(domain=domain, status=status)
        return [self.to_badcase(r) for r in rows]

    async def create_badcase(self, user: User, body: BadCaseCreate) -> BadCasePublic:
        row = BadCase(
            id=str(uuid.uuid4()),
            title=body.title.strip(),
            category=body.category,
            domain=body.domain,
            intent=body.intent,
            severity=body.severity,
            status="open",
            description=body.description,
            root_cause=body.root_cause,
            suggestion=body.suggestion,
            session_id=body.session_id,
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.add_badcase(row)
        await write_audit(self.db, user, action="登记 Bad Case", target=f"{row.id} {row.title}")
        return self.to_badcase(row)

    async def update_badcase(
        self, user: User, case_id: str, body: BadCaseUpdate
    ) -> BadCasePublic:
        row = await self.repo.get_badcase(case_id)
        if row is None:
            raise FileNotFoundError("Bad Case 不存在")
        data = body.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _now()
        await self.db.flush()
        await write_audit(
            self.db,
            user,
            action="更新 Bad Case",
            target=f"{row.id} → {row.status}",
        )
        return self.to_badcase(row)

    # --- audit / rbac / metrics ---
    async def list_audits(
        self, *, operator: str | None = None, action: str | None = None, limit: int = 100
    ) -> list[AuditLogPublic]:
        rows = await self.repo.list_audits(operator=operator, action=action, limit=limit)
        return [self.to_audit(r) for r in rows]

    def rbac_matrix(self) -> dict[str, Any]:
        roles = ["员工", "坐席", "运营管理员"]
        permissions = [
            {"key": "chat", "label": "智能对话"},
            {"key": "services", "label": "服务大厅"},
            {"key": "agent_queue", "label": "坐席队列"},
            {"key": "agent_session", "label": "会话工作台"},
            {"key": "ops_knowledge", "label": "知识管理"},
            {"key": "ops_config", "label": "运营配置"},
            {"key": "ops_security", "label": "权限审计"},
        ]
        matrix = {
            "员工": {
                "chat": True,
                "services": True,
                "agent_queue": False,
                "agent_session": False,
                "ops_knowledge": False,
                "ops_config": False,
                "ops_security": False,
            },
            "坐席": {
                "chat": False,
                "services": False,
                "agent_queue": True,
                "agent_session": True,
                "ops_knowledge": False,
                "ops_config": False,
                "ops_security": False,
            },
            "运营管理员": {
                "chat": False,
                "services": False,
                "agent_queue": True,
                "agent_session": True,
                "ops_knowledge": True,
                "ops_config": True,
                "ops_security": True,
            },
        }
        return {"roles": roles, "permissions": permissions, "matrix": matrix}

    async def metrics_summary(self) -> MetricsSummary:
        now = _now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        sessions_today = (
            await self.db.execute(
                select(func.count()).select_from(ChatSession).where(
                    ChatSession.created_at >= day_start
                )
            )
        ).scalar_one()

        sessions_total = (
            await self.db.execute(select(func.count()).select_from(ChatSession))
        ).scalar_one()
        tickets_total = (
            await self.db.execute(select(func.count()).select_from(Ticket))
        ).scalar_one()
        tickets_waiting = (
            await self.db.execute(
                select(func.count())
                .select_from(Ticket)
                .where(Ticket.status == "waiting")
            )
        ).scalar_one()
        knowledge_published = (
            await self.db.execute(
                select(func.count())
                .select_from(KnowledgeDocument)
                .where(KnowledgeDocument.status == "published")
            )
        ).scalar_one()
        tasks_open = (
            await self.db.execute(
                select(func.count())
                .select_from(Task)
                .where(Task.status.in_(("pending_approve", "processing", "need_materials")))
            )
        ).scalar_one()
        badcases_open = await self.repo.count_badcases(status="open")

        st = int(sessions_total or 0)
        tt = int(tickets_total or 0)
        handoff_rate = round((tt / st) * 100, 1) if st else 0.0
        ai_resolve_rate = round(max(0.0, 100.0 - handoff_rate), 1)

        # 近 7 日会话量（按创建日聚合，缺日补 0）
        labels: list[str] = []
        trend: list[int] = []
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            labels.append(d.strftime("%m-%d"))
            d0 = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            d1 = d0 + timedelta(days=1)
            cnt = (
                await self.db.execute(
                    select(func.count())
                    .select_from(ChatSession)
                    .where(ChatSession.created_at >= d0, ChatSession.created_at < d1)
                )
            ).scalar_one()
            trend.append(int(cnt or 0))

        return MetricsSummary(
            sessions_today=int(sessions_today or 0),
            ai_resolve_rate=ai_resolve_rate,
            handoff_rate=handoff_rate,
            avg_satisfaction=4.6,
            knowledge_published=int(knowledge_published or 0),
            tasks_open=int(tasks_open or 0),
            tickets_waiting=int(tickets_waiting or 0),
            badcases_open=int(badcases_open or 0),
            trend_sessions=trend,
            trend_labels=labels,
        )
