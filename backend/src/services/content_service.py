"""内容产出服务：改写 / 报告 / 权限内数据导出。"""

from __future__ import annotations

import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone

from pycore.core import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    AuditLog,
    BadCase,
    ContentArtifact,
    KnowledgeDocument,
    Task,
    Ticket,
    User,
)
from src.models.content import (
    ContentArtifactPublic,
    ContentCapabilities,
    ExportDataset,
    ExportRequest,
    ReportRequest,
    RewriteRequest,
)
from src.repositories.content import ContentRepository
from src.repositories.qa import QaRepository
from src.services import llm_client
from src.services.ops_service import write_audit

logger = get_logger()

TONE_LABEL = {"formal": "正式规范", "concise": "简洁干练", "friendly": "友好清晰"}

# 演示三角色能力（对齐 PRD §2.1）
ROLE_EXPORT: dict[str, list[ExportDataset]] = {
    "employee": ["my_tasks", "my_tickets"],
    "agent": ["agent_tickets", "qa_followups"],
    "admin": ["knowledge", "bad_cases", "audit_logs"],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_filename(name: str, ext: str) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", name.strip())[:40] or "artifact"
    return f"{base}.{ext}"


class ContentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContentRepository(db)

    def capabilities(self, user: User) -> ContentCapabilities:
        role = user.role
        datasets = ROLE_EXPORT.get(role, [])
        notes = [
            "不可用本能力办理报销/请假等事务（仍走 Skill 确认闸）",
            "禁止导出薪资、证件号、银行卡等敏感明文",
            "完整 PPT 可视化编辑器属 V1.1；本版报告为 Markdown",
        ]
        if role == "employee":
            notes.append("员工仅可导出本人任务/工单")
        elif role == "agent":
            notes.append("坐席仅可导出本人经办工单与质检回访")
        elif role == "admin":
            notes.append("运营可导出知识/Bad Case/审计清单；管理者聚合能力在本演示账号合并展示")
        return ContentCapabilities(
            can_rewrite=role in ("employee", "agent", "admin"),
            can_report=role in ("employee", "agent", "admin"),
            export_datasets=datasets,
            notes=notes,
        )

    def to_public(self, row: ContentArtifact) -> ContentArtifactPublic:
        return ContentArtifactPublic(
            id=row.id,
            kind=row.kind,  # type: ignore[arg-type]
            title=row.title,
            summary=row.summary,
            body=row.body,
            mime=row.mime,
            download_name=row.download_name,
            task_id=row.task_id,
            owner_role=row.owner_role,
            created_at=row.created_at or _now(),
        )

    async def list_mine(self, user: User) -> list[ContentArtifactPublic]:
        rows = await self.repo.list_for_owner(user.id)
        return [self.to_public(r) for r in rows]

    async def get_mine(self, user: User, artifact_id: str) -> ContentArtifactPublic:
        row = await self.repo.get(artifact_id)
        if row is None or row.owner_id != user.id:
            raise FileNotFoundError("产出不存在")
        return self.to_public(row)

    async def _save(
        self,
        user: User,
        *,
        kind: str,
        title: str,
        summary: str,
        body: str,
        mime: str,
        download_name: str,
        meta: dict,
        task_id: str | None = None,
    ) -> ContentArtifact:
        row = ContentArtifact(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            owner_role=user.role,
            kind=kind,
            title=title,
            summary=summary[:500],
            body=body,
            mime=mime,
            download_name=download_name,
            task_id=task_id,
            meta_json=json.dumps(meta, ensure_ascii=False),
            created_at=_now(),
        )
        await self.repo.create(row)
        await write_audit(
            self.db,
            user,
            action=f"内容产出-{kind}",
            target=f"{row.id} {title}",
        )
        return row

    async def rewrite(self, user: User, body: RewriteRequest) -> ContentArtifactPublic:
        caps = self.capabilities(user)
        if not caps.can_rewrite:
            raise PermissionError("当前角色不可使用文档改写")

        tone = TONE_LABEL.get(body.tone, "正式规范")
        system = (
            "你是企业内部行政文书助手。请改写用户文稿，保持事实不变，"
            f"语气要求：{tone}。输出纯中文正文，不要解释过程。"
            "不要编造制度条款；涉及制度处标注「草稿待核对」。"
        )
        try:
            if llm_client.llm_configured():
                text = await llm_client.chat_completion(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": body.text.strip()},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )
            else:
                raise RuntimeError("LLM 未配置")
        except Exception as exc:  # noqa: BLE001
            logger.warning("rewrite fallback template: {}", exc)
            text = (
                f"【改写草稿 · {tone} · 模板降级】\n\n"
                f"{body.text.strip()}\n\n"
                "——\n已按对内文书体例整理结构（未连接模型时为模板占位）。"
                "正式发文前请人工核对。"
            )

        md = f"# {body.title}\n\n{text}\n"
        row = await self._save(
            user,
            kind="rewrite",
            title=body.title,
            summary=text[:120],
            body=md,
            mime="text/markdown",
            download_name=_safe_filename(body.title, "md"),
            meta={"tone": body.tone},
        )
        return self.to_public(row)

    async def report(self, user: User, body: ReportRequest) -> ContentArtifactPublic:
        caps = self.capabilities(user)
        if not caps.can_report:
            raise PermissionError("当前角色不可生成报告")

        role_hint = {
            "employee": "面向个人办事小结，勿写全司数据。",
            "agent": "面向坐席个案或班次小结，勿导出他人隐私明细。",
            "admin": "面向知识/运营治理周报，制度引用须标明草稿待核对。",
        }.get(user.role, "")

        system = (
            "你是太平洋金科行政报告助手。根据主题生成结构化 Markdown 报告："
            "含摘要、背景、要点、建议、风险与待核对项。"
            f"{role_hint} 不要编造未提供的数字；缺失处写「待补充」。"
        )
        user_prompt = f"主题：{body.topic.strip()}\n补充要点：\n{body.points.strip() or '（无）'}"
        try:
            if llm_client.llm_configured():
                text = await llm_client.chat_completion(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.35,
                    max_tokens=2500,
                )
            else:
                raise RuntimeError("LLM 未配置")
        except Exception as exc:  # noqa: BLE001
            logger.warning("report fallback template: {}", exc)
            text = (
                f"# {body.title}\n\n"
                f"## 摘要\n围绕「{body.topic}」的行政报告草稿（模板降级）。\n\n"
                f"## 要点\n{body.points.strip() or '- 待补充'}\n\n"
                "## 建议\n- 请人工核对数据与制度依据后再外发。\n\n"
                "## 风险与待核对\n- 本稿未连接大模型，内容为占位结构。\n"
            )

        if not text.lstrip().startswith("#"):
            text = f"# {body.title}\n\n{text}"
        row = await self._save(
            user,
            kind="report",
            title=body.title,
            summary=body.topic[:120],
            body=text,
            mime="text/markdown",
            download_name=_safe_filename(body.title, "md"),
            meta={"topic": body.topic},
        )
        return self.to_public(row)

    async def export(self, user: User, body: ExportRequest) -> ContentArtifactPublic:
        allowed = ROLE_EXPORT.get(user.role, [])
        if body.dataset not in allowed:
            raise PermissionError("当前角色不可导出该数据集")

        # 敏感关键字硬拦截（标题层面）
        banned = ("薪资", "工资", "银行卡", "身份证", "证件号")
        if any(x in body.title for x in banned):
            raise PermissionError("禁止导出薪资/证件等敏感类别")

        headers, rows = await self._build_export_rows(user, body.dataset)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        csv_text = buf.getvalue()
        summary = f"{body.dataset} · {len(rows)} 行"
        row = await self._save(
            user,
            kind="export",
            title=body.title,
            summary=summary,
            body=csv_text,
            mime="text/csv",
            download_name=_safe_filename(body.title, "csv"),
            meta={"dataset": body.dataset, "rows": len(rows)},
        )
        return self.to_public(row)

    async def _build_export_rows(
        self, user: User, dataset: ExportDataset
    ) -> tuple[list[str], list[list[str]]]:
        if dataset == "my_tasks":
            result = await self.db.execute(
                select(Task)
                .where(Task.applicant_id == user.id)
                .order_by(Task.updated_at.desc())
                .limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "title", "status", "service_name", "updated_at"]
            rows = [
                [
                    t.id[:8],
                    t.title,
                    t.status,
                    t.service_name,
                    (t.updated_at or _now()).isoformat(),
                ]
                for t in items
            ]
            return headers, rows

        if dataset == "my_tickets":
            result = await self.db.execute(
                select(Ticket)
                .where(Ticket.employee_id == user.id)
                .order_by(Ticket.updated_at.desc())
                .limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "subject", "status", "agent_name", "updated_at"]
            rows = [
                [
                    t.id[:8],
                    t.subject,
                    t.status,
                    t.agent_name or "",
                    (t.updated_at or _now()).isoformat(),
                ]
                for t in items
            ]
            return headers, rows

        if dataset == "agent_tickets":
            result = await self.db.execute(
                select(Ticket)
                .where(Ticket.agent_id == user.id)
                .order_by(Ticket.updated_at.desc())
                .limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "subject", "status", "employee_name", "updated_at"]
            rows = [
                [
                    t.id[:8],
                    t.subject,
                    t.status,
                    t.employee_name,
                    (t.updated_at or _now()).isoformat(),
                ]
                for t in items
            ]
            return headers, rows

        if dataset == "qa_followups":
            qa = QaRepository(self.db)
            followups = await qa.list_followups()
            # 坐席可见全部回访种子（演示）；生产可再按 agent 过滤
            headers = ["id", "type", "status", "due_date", "assignee", "employee"]
            rows = [
                [
                    f.id[:8],
                    f.type,
                    f.status,
                    f.due_date or "",
                    f.assignee or "",
                    f.employee_name or "",
                ]
                for f in followups[:200]
            ]
            return headers, rows

        if dataset == "knowledge":
            result = await self.db.execute(
                select(KnowledgeDocument)
                .order_by(KnowledgeDocument.updated_at.desc())
                .limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "title", "status", "category", "version"]
            rows = [
                [d.id[:8], d.title, d.status, d.category, d.version] for d in items
            ]
            return headers, rows

        if dataset == "bad_cases":
            result = await self.db.execute(
                select(BadCase).order_by(BadCase.created_at.desc()).limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "title", "category", "status", "created_at"]
            rows = [
                [
                    b.id[:8],
                    b.title,
                    b.category,
                    b.status,
                    (b.created_at or _now()).isoformat(),
                ]
                for b in items
            ]
            return headers, rows

        if dataset == "audit_logs":
            result = await self.db.execute(
                select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
            )
            items = list(result.scalars().all())
            headers = ["id", "operator", "role", "action", "target", "result", "created_at"]
            rows = [
                [
                    a.id[:8],
                    a.operator,
                    a.role,
                    a.action,
                    a.target,
                    a.result,
                    (a.created_at or _now()).isoformat(),
                ]
                for a in items
            ]
            return headers, rows

        raise ValueError("未知数据集")
