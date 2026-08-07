"""服务目录：种子与查询。"""

from __future__ import annotations

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ServiceCatalog
from src.models.catalog import ServicePublic
from src.repositories.catalog import CatalogRepository

logger = get_logger()

SEED_SERVICES = (
    {
        "id": "expense",
        "name": "费用报销",
        "domain": "expense",
        "domain_label": "费用报销",
        "priority": "P0",
        "description": "材料预检 + 发起办理",
        "action": "问 Agent / 表单",
        "can_apply": True,
    },
    {
        "id": "leave",
        "name": "年假申请",
        "domain": "hr",
        "domain_label": "HR",
        "priority": "P0",
        "description": "余额查询与请假确认卡",
        "action": "问 Agent / 表单",
        "can_apply": True,
    },
    {
        "id": "repair",
        "name": "IT 故障报修",
        "domain": "it",
        "domain_label": "IT",
        "priority": "P0",
        "description": "建单与进度跟踪",
        "action": "问 Agent / 表单",
        "can_apply": True,
    },
    {
        "id": "meeting",
        "name": "会议室预订",
        "domain": "admin",
        "domain_label": "行政办公",
        "priority": "P0",
        "description": "时段冲突校验",
        "action": "问 Agent / 表单",
        "can_apply": True,
    },
    {
        "id": "travel-qa",
        "name": "差旅标准问答",
        "domain": "travel",
        "domain_label": "差旅",
        "priority": "P1",
        "description": "制度问答带来源",
        "action": "问 Agent",
        "can_apply": False,
    },
    {
        "id": "visitor",
        "name": "访客预约",
        "domain": "admin",
        "domain_label": "行政办公",
        "priority": "P1",
        "description": "访客信息登记",
        "action": "表单",
        "can_apply": True,
    },
    {
        "id": "asset",
        "name": "资产申购",
        "domain": "asset",
        "domain_label": "资产采购",
        "priority": "P2",
        "description": "预审材料",
        "action": "问 Agent",
        "can_apply": False,
    },
    {
        "id": "handoff",
        "name": "转人工服务台",
        "domain": "desk",
        "domain_label": "服务台",
        "priority": "P0",
        "description": "低置信 / 复杂诉求",
        "action": "@ 转人工",
        "can_apply": False,
    },
    {
        "id": "planner-demo",
        "name": "开放式材料任务（Planner）",
        "domain": "material",
        "domain_label": "开放材料",
        "priority": "P2",
        "description": "Planner 占位任务入口",
        "action": "表单",
        "can_apply": True,
    },
)


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CatalogRepository(db)

    def to_public(self, item: ServiceCatalog) -> ServicePublic:
        return ServicePublic(
            id=item.id,
            name=item.name,
            domain=item.domain,
            domain_label=item.domain_label,
            priority=item.priority,  # type: ignore[arg-type]
            description=item.description,
            action=item.action,
            can_apply=item.can_apply,
        )

    async def list_services(self, domain: str | None = None) -> list[ServicePublic]:
        items = await self.repo.list_enabled()
        if domain and domain != "all":
            items = [i for i in items if i.domain == domain]
        return [self.to_public(i) for i in items]

    async def get(self, service_id: str) -> ServiceCatalog:
        item = await self.repo.get(service_id)
        if item is None or not item.enabled:
            raise FileNotFoundError("服务不存在")
        return item

    async def ensure_seed(self) -> None:
        if await self.repo.count() > 0:
            return
        for raw in SEED_SERVICES:
            await self.repo.create(ServiceCatalog(**raw, enabled=True))
        logger.info("Service catalog seeded", count=len(SEED_SERVICES))
