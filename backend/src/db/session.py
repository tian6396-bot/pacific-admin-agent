"""异步数据库引擎与会话。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import BACKEND_ROOT, settings
from src.db.models import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _resolve_sqlite_url(url: str) -> str:
    """将相对路径 SQLite URL 锚定到 backend/ 目录。"""
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return url
    rest = url[len(prefix) :]
    if rest.startswith("./") or (not rest.startswith("/") and "://" not in rest):
        abs_path = (BACKEND_ROOT / rest.lstrip("./")).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return f"{prefix}{abs_path}"
    return url


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = _resolve_sqlite_url(settings.database_url)
        _engine = create_async_engine(url, echo=settings.debug)
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """创建数据目录并建表。"""
    for rel in (settings.upload_dir, settings.vector_index_dir):
        path = Path(rel)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        path.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
