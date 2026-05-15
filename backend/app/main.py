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
        await tg_adapter.start()
        logger.info("✅ Telegram Bot 已启动")
    else:
        logger.warning("⚠️ TG_BOT_TOKEN 未配置，Telegram Bot 未启动")

    # TODO: 启动定时任务调度器
    yield

    logger.info("👋 应用关闭中...")
    if settings.TG_BOT_TOKEN:
        from app.services.platform.telegram import tg_adapter
        await tg_adapter.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 情感陪聊机器人 — 兼容酒馆角色卡/世界书/预设，多平台·多模态·主动交互",
    lifespan=lifespan,
)

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
