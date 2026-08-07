"""健康检查。"""

from fastapi import APIRouter

from pycore.api.responses import success_response
from src.core.config import settings
from src.services.llm_client import llm_status

router = APIRouter(tags=["health"])


@router.get("/health")
async def api_health():
    """供前端 `/api` 前缀与联调使用的健康检查。"""
    return success_response(
        data={
            "status": "ok",
            "app": "pacific-admin-agent",
            "debug": settings.debug,
            "database": "configured",
            "llm": llm_status(),
        },
        message="service healthy",
    )
