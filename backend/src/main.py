"""应用入口：PyCore APIServer。"""

from pycore.api import APIConfig, APIServer
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger

from src.api.routes.agent_queue import router as agent_queue_router
from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.chat_ws import router as chat_ws_router
from src.api.routes.health import router as health_router
from src.api.routes.knowledge import router as knowledge_router
from src.api.routes.materials import router as materials_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.ops import router as ops_router
from src.api.routes.preferences import router as preferences_router
from src.api.routes.qa import router as qa_router
from src.api.routes.services import router as services_router
from src.api.routes.skills import router as skills_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.tickets import router as tickets_router
from src.api.routes.tools import router as tools_router
from src.core.config import settings
from src.db.session import close_db, get_session_factory, init_db
from src.services.auth_service import AuthService
from src.services.catalog_service import CatalogService
from src.services.knowledge_service import KnowledgeService
from src.services.ops_service import OpsService
from src.services.qa_service import QaService
from src.services.skill_service import SkillService

Logger.configure(
    LoggerConfig(
        level=LogLevel.DEBUG if settings.debug else LogLevel.INFO,
        app_name="pacific-admin-agent",
        json_format=False,
    )
)
logger = get_logger()


async def on_startup() -> None:
    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        if settings.seed_demo_users:
            await AuthService(session).ensure_demo_users()
            await KnowledgeService(session).ensure_demo_knowledge()
        else:
            await KnowledgeService(session).sync_published_index()
        await CatalogService(session).ensure_seed()
        await SkillService(session).ensure_seed()
        await OpsService(session).ensure_seed()
        await QaService(session).ensure_seed()
        await session.commit()
    logger.info("Startup complete", seed_users=settings.seed_demo_users)


server = APIServer(
    APIConfig(
        title="太平洋金科·智能行政咨询助手 API",
        description="Pacific Admin Agent Backend",
        version="0.1.0",
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        cors_origins=settings.cors_origins,
    )
)

server.on_startup(on_startup)
server.on_shutdown(close_db)
server.include_router(health_router, prefix="/api")
server.include_router(auth_router, prefix="/api")
server.include_router(knowledge_router, prefix="/api")
server.include_router(chat_router, prefix="/api")
server.include_router(chat_ws_router, prefix="/api")
server.include_router(services_router, prefix="/api")
server.include_router(tasks_router, prefix="/api")
server.include_router(tickets_router, prefix="/api")
server.include_router(agent_queue_router, prefix="/api")
server.include_router(skills_router, prefix="/api")
server.include_router(tools_router, prefix="/api")
server.include_router(ops_router, prefix="/api")
server.include_router(materials_router, prefix="/api")
server.include_router(qa_router, prefix="/api")
server.include_router(notifications_router, prefix="/api")
server.include_router(preferences_router, prefix="/api")

app = server.app
logger.info(
    "App factory ready",
    host=settings.host,
    port=settings.port,
    cors=settings.cors_origins,
)
