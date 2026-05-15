"""NestTalk 主应用入口"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from app.core.config import settings
from app.core.database import init_db
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info(f"🪹 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")

    if settings.TG_BOT_TOKEN:
        from app.services.platform.telegram import tg_adapter
        if tg_adapter:
            await tg_adapter.start()
            logger.info("✅ Telegram Bot 已启动")
        else:
            logger.warning("⚠️ Telegram Bot 初始化失败")
    else:
        logger.warning("⚠️ TG_BOT_TOKEN 未配置")

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
ADMIN_PASSWORD = "nesttalk2026"


# ─── API 路由（必须在 Catch-all 前注册）─────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@app.get("/api/info")
async def app_info():
    return {
        "name": settings.APP_NAME, "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER, "llm_model": settings.LLM_MODEL,
    }

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    if data.get("password") == ADMIN_PASSWORD:
        return {"success": True, "token": ADMIN_PASSWORD}
    return {"success": False, "message": "密码错误"}

# 业务 API 路由
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


# ─── 管理面板（SPA Catch-all，必须在最后）─────────

@app.get("/", response_class=HTMLResponse)
async def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(path):
        return FileResponse(path)
    return "<h1>NestTalk</h1>"


@app.get("/{path:path}")
async def serve_static(path: str):
    """静态文件 & SPA 兜底"""
    # 跳过不存在的 API 路径
    if path.startswith("api/"):
        return {"error": "not found", "path": path}

    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # SPA 兜底
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>NestTalk - 栖言</h1>")
