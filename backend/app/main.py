"""NestTalk 主应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info(f"🪹 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")

    # 启动 Telegram Bot
    if settings.TG_BOT_TOKEN:
        from app.services.platform.telegram import tg_adapter
        if tg_adapter:
            await tg_adapter.start()
            logger.info("✅ Telegram Bot 已启动")
        else:
            logger.warning("⚠️ Telegram Bot 初始化失败，检查 Token")
    else:
        logger.warning("⚠️ TG_BOT_TOKEN 未配置，Telegram Bot 未启动")

    # TODO: 启动定时任务调度器
    yield

    logger.info("👋 应用关闭中...")
    if settings.TG_BOT_TOKEN:
        from app.services.platform.telegram import tg_adapter
        if tg_adapter:
            await tg_adapter.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="心有归栖，万事可轻言 — AI 情感陪聊机器人",
    lifespan=lifespan,
)

# 注册路由
from app.api.characters import router as characters_router
from app.api.worldbooks import router as worldbooks_router
from app.api.presets import router as presets_router
from app.api.chat import router as chat_router
from app.api.backup import router as backup_router
from app.api.memories import router as memories_router

app.include_router(characters_router)
app.include_router(worldbooks_router)
app.include_router(presets_router)
app.include_router(chat_router)
app.include_router(backup_router)
app.include_router(memories_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/info")
async def app_info():
    """应用信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
    }
