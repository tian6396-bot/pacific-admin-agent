"""工具契约列表。"""

from fastapi import APIRouter

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.services.skill_service import SkillService

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools(db: DbSession, user: CurrentUser):
    _ = user
    items = await SkillService(db).list_tools()
    return success_response(data=[i.model_dump(mode="json") for i in items])
