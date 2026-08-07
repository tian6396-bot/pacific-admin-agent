"""应用配置：从 backend/.env 文件加载（不读取进程环境变量）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pycore.core import BaseSettings, ConfigManager

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"


class AppSettings(BaseSettings):
    """B0+ 全局配置。"""

    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8010
    cors_origins: list[str] = ["http://localhost:5173"]

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    jwt_secret: str = "change-me-dev"
    jwt_expire_minutes: int = 1440

    upload_dir: str = "./data/uploads"
    vector_index_dir: str = "./data/faiss"

    qa_similarity_threshold: float = 0.8
    short_memory_turns: int = 3
    intent_confidence_threshold: float = 0.7

    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model_embedding: str = ""
    llm_model_intent: str = ""
    llm_model_generate: str = ""
    llm_model_rerank: str = ""

    seed_demo_users: bool = True


def _coerce_value(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    lower = text.lower()
    if lower in {"true", "yes", "1"}:
        return True
    if lower in {"false", "no", "0"}:
        return False
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _parse_env_file(path: Path) -> dict[str, Any]:
    """读取 .env 文件为字典，不依赖 os.environ。"""
    if not path.exists():
        return {}

    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key.lower()] = _coerce_value(value)
    return result


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    raw = _parse_env_file(ENV_FILE)
    known = {name: raw[name] for name in AppSettings.model_fields if name in raw}
    manager: ConfigManager[AppSettings] = ConfigManager()
    manager.load_from_dict(AppSettings, known)
    return manager.settings


settings = get_settings()
