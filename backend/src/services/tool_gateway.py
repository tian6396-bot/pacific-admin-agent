"""工具网关：默认 Mock，禁止静默写真实外部系统。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from pycore.core import get_logger

from src.db.models import ToolDef

logger = get_logger()


class ToolGateway:
    """仅调用已登记工具；mock_enabled 时直接返回种子 Mock 响应。"""

    async def invoke(
        self,
        tool: ToolDef,
        *,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if tool.status != "active":
            raise ValueError(f"工具已禁用：{tool.id}")

        key = idempotency_key or str(uuid.uuid4())
        logger.info(
            "Tool invoke",
            tool_id=tool.id,
            mock=tool.mock_enabled,
            idempotency_key=key,
        )

        if tool.mock_enabled:
            try:
                body = json.loads(tool.mock_response or "{}")
            except json.JSONDecodeError:
                body = {"code": 0, "message": "mock ok", "data": {}}
            if not isinstance(body, dict):
                body = {"code": 0, "data": body}
            body.setdefault("mock", True)
            body.setdefault("idempotency_key", key)
            body.setdefault("request_echo", payload)
            return body

        # 真实 HTTP 留扩展点：本阶段强制要求 mock，避免误写
        raise ValueError(
            f"工具 {tool.id} 未开启 Mock，且本环境禁止直连外部写接口。请在运营配置开启 Mock。"
        )
