"""服务目录路由。"""

from fastapi import APIRouter, Query

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.services.catalog_service import CatalogService

router = APIRouter(prefix="/services", tags=["services"])


@router.get("")
async def list_services(
    db: DbSession,
    user: CurrentUser,
    domain: str | None = Query(default=None),
):
    _ = user
    items = await CatalogService(db).list_services(domain=domain)
    return success_response(data=[i.model_dump(mode="json") for i in items])
