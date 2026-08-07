"""百炼 / OpenAI 兼容 Chat Completions 客户端。

配置来自 backend/.env（AppSettings），不读取进程环境变量。
httpx 显式 trust_env=False，避免继承代理等环境配置。
"""

from __future__ import annotations

from typing import Any

from pycore.core import get_logger

from src.core.config import settings

logger = get_logger()


def _httpx():
    """延迟导入：未安装 httpx 时仍允许登录等非 LLM 接口启动。"""
    try:
        import httpx
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "缺少依赖 httpx。请执行：pip install 'httpx>=0.27' 后重启后端"
        ) from exc
    return httpx


def llm_configured() -> bool:
    return bool(settings.llm_api_key and settings.llm_base_url and settings.llm_model_generate)


def llm_status() -> dict[str, Any]:
    return {
        "configured": llm_configured(),
        "base_url": settings.llm_base_url or None,
        "model_generate": settings.llm_model_generate or None,
        "model_intent": settings.llm_model_intent or None,
        "model_embedding": settings.llm_model_embedding or None,
    }


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """调用 OpenAI 兼容 /chat/completions，返回助手文本。"""
    if not settings.llm_api_key or not settings.llm_base_url:
        raise RuntimeError("LLM 未配置：请在 backend/.env 填写 LLM_API_KEY 与 LLM_BASE_URL")

    use_model = (model or settings.llm_model_generate or "").strip()
    if not use_model:
        raise RuntimeError("LLM 未配置：请填写 LLM_MODEL_GENERATE")

    httpx = _httpx()
    base = settings.llm_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    payload = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
        resp = await client.post(url, json=payload, headers=headers)
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"LLM 响应非 JSON：HTTP {resp.status_code}") from exc

        if resp.status_code >= 400:
            err = data.get("error") if isinstance(data, dict) else None
            detail = err.get("message") if isinstance(err, dict) else str(data)[:300]
            raise RuntimeError(f"LLM 调用失败 HTTP {resp.status_code}: {detail}")

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"LLM 响应结构异常: {str(data)[:300]}") from exc

        text = (content or "").strip()
        if not text:
            raise RuntimeError("LLM 返回空内容")
        return text
