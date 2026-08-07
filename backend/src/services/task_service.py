"""任务：申请建单、列表、详情、审批与时间线。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from pycore.core import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Task, TaskEvent, User
from src.models.catalog import (
    TaskActionRequest,
    TaskApplyRequest,
    TaskDetail,
    TaskEventPublic,
    TaskPublic,
    TaskTab,
)
from src.repositories.catalog import TaskRepository
from src.repositories.user import UserRepository
from src.services.catalog_service import CatalogService

logger = get_logger()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_form(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _tab_for(task: Task, viewer_id: str) -> TaskTab:
    if task.kind == "planner":
        return "planner"
    if task.status in ("done", "rejected", "cancelled"):
        return "history"
    if (
        task.status == "pending_approve"
        and task.approver_id == viewer_id
        and task.applicant_id != viewer_id
    ):
        return "approve"
    return "active"


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TaskRepository(db)
        self.catalog = CatalogService(db)
        self.users = UserRepository(db)

    def to_public(self, task: Task, viewer_id: str) -> TaskPublic:
        return TaskPublic(
            id=task.id,
            title=task.title,
            service_id=task.service_id,
            service_name=task.service_name,
            domain_label=task.domain_label,
            kind=task.kind,  # type: ignore[arg-type]
            status=task.status,  # type: ignore[arg-type]
            tab=_tab_for(task, viewer_id),
            applicant_name=task.applicant_name,
            approver_name=task.approver_name,
            form=_parse_form(task.form_json),
            created_at=task.created_at or _now(),
            updated_at=task.updated_at or _now(),
        )

    def to_detail(self, task: Task, viewer_id: str) -> TaskDetail:
        base = self.to_public(task, viewer_id)
        events = [
            TaskEventPublic(
                id=e.id,
                time=e.created_at or _now(),
                title=e.title,
                desc=e.desc,
                done=e.done,
            )
            for e in (task.events or [])
        ]
        return TaskDetail(**base.model_dump(), events=events)

    async def _default_approver(self) -> User | None:
        agent = await self.users.get_by_username("agent")
        if agent:
            return agent
        result = await self.db.execute(select(User).where(User.role == "agent").limit(1))
        return result.scalar_one_or_none()

    async def apply(self, user: User, body: TaskApplyRequest) -> TaskDetail:
        service = await self.catalog.get(body.service_id)
        if not service.can_apply:
            raise ValueError("该服务不支持在线申请，请改问 Agent 或转人工")

        kind = "planner" if service.id == "planner-demo" or service.domain == "material" else "skill"
        approver = await self._default_approver()
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title=body.title.strip(),
            service_id=service.id,
            service_name=service.name,
            domain_label=service.domain_label,
            kind=kind,
            status="pending_approve" if kind == "skill" else "processing",
            applicant_id=user.id,
            applicant_name=user.name,
            approver_id=approver.id if approver and kind == "skill" else None,
            approver_name=approver.name if approver and kind == "skill" else None,
            form_json=json.dumps(body.form or {}, ensure_ascii=False),
            created_at=_now(),
            updated_at=_now(),
        )
        await self.repo.create(task)

        await self.repo.add_event(
            TaskEvent(
                id=str(uuid.uuid4()),
                task_id=task_id,
                title="创建任务",
                desc=f"{user.name} 通过服务申请提交「{service.name}」",
                done=True,
                created_at=_now(),
            )
        )
        if kind == "skill":
            await self.repo.add_event(
                TaskEvent(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    title="AI 预审",
                    desc="表单已接收；演示环境跳过外部工具，进入审批队列",
                    done=True,
                    created_at=_now(),
                )
            )
            await self.repo.add_event(
                TaskEvent(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    title="待审批",
                    desc=f"等待 {(approver.name if approver else '审批人')} 处理",
                    done=False,
                    created_at=_now(),
                )
            )
        else:
            await self.repo.add_event(
                TaskEvent(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    title="Planner 占位执行",
                    desc="MVP 仅建任务与进度占位，完整 Planner 见后续版本",
                    done=False,
                    created_at=_now(),
                )
            )

        task = await self.repo.get(task_id)
        assert task is not None
        logger.info("Task created", task_id=task_id, service=service.id)
        return self.to_detail(task, user.id)

    async def list(self, user: User, tab: str | None = None) -> list[TaskPublic]:
        tasks = await self.repo.list_for_user(user_id=user.id, tab=tab)
        return [self.to_public(t, user.id) for t in tasks]

    async def get(self, user: User, task_id: str) -> TaskDetail:
        task = await self.repo.get(task_id)
        if task is None:
            raise FileNotFoundError("任务不存在")
        if user.id not in (task.applicant_id, task.approver_id) and user.role != "admin":
            raise PermissionError("无权查看该任务")
        return self.to_detail(task, user.id)

    async def _mark_pending_event_done(self, task: Task) -> None:
        for event in task.events or []:
            if not event.done:
                event.done = True

    async def approve(self, user: User, task_id: str, body: TaskActionRequest) -> TaskDetail:
        task = await self.repo.get(task_id)
        if task is None:
            raise FileNotFoundError("任务不存在")
        if task.approver_id != user.id and user.role != "admin":
            raise PermissionError("仅审批人可操作")
        if task.status != "pending_approve":
            raise ValueError("当前状态不可审批")

        await self._mark_pending_event_done(task)
        task.status = "done"
        task.updated_at = _now()
        comment = (body.comment or "").strip()
        await self.repo.add_event(
            TaskEvent(
                id=str(uuid.uuid4()),
                task_id=task.id,
                title="审批通过",
                desc=comment or f"{user.name} 已通过（演示办结）",
                done=True,
                created_at=_now(),
            )
        )
        await self.db.flush()
        from src.services.ops_service import write_audit

        await write_audit(
            self.db,
            user,
            action="任务审批通过",
            target=f"{task.id} {task.title}",
        )
        task = await self.repo.get(task_id)
        assert task is not None
        return self.to_detail(task, user.id)

    async def reject(self, user: User, task_id: str, body: TaskActionRequest) -> TaskDetail:
        task = await self.repo.get(task_id)
        if task is None:
            raise FileNotFoundError("任务不存在")
        if task.approver_id != user.id and user.role != "admin":
            raise PermissionError("仅审批人可操作")
        if task.status != "pending_approve":
            raise ValueError("当前状态不可驳回")

        await self._mark_pending_event_done(task)
        task.status = "rejected"
        task.updated_at = _now()
        comment = (body.comment or "").strip()
        await self.repo.add_event(
            TaskEvent(
                id=str(uuid.uuid4()),
                task_id=task.id,
                title="审批驳回",
                desc=comment or f"{user.name} 已驳回",
                done=True,
                created_at=_now(),
            )
        )
        await self.db.flush()
        task = await self.repo.get(task_id)
        assert task is not None
        return self.to_detail(task, user.id)

    async def request_materials(self, user: User, task_id: str) -> TaskDetail:
        """申请人自助标记需补充材料（演示）。"""
        task = await self.repo.get(task_id)
        if task is None:
            raise FileNotFoundError("任务不存在")
        if task.applicant_id != user.id:
            raise PermissionError("仅申请人可操作")
        if task.status in ("done", "rejected", "cancelled"):
            raise ValueError("已结束任务不可再改")

        await self._mark_pending_event_done(task)
        task.status = "need_materials"
        task.updated_at = _now()
        await self.repo.add_event(
            TaskEvent(
                id=str(uuid.uuid4()),
                task_id=task.id,
                title="待补充材料",
                desc="请前往材料中心上传相关附件",
                done=False,
                created_at=_now(),
            )
        )
        await self.db.flush()
        task = await self.repo.get(task_id)
        assert task is not None
        return self.to_detail(task, user.id)
