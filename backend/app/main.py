"""NestTalk 主应用入口"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from app.core.config import settings
from app.core.database import init_db
from loguru import logger


def _read_admin_password() -> str:
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("ADMIN_PASSWORD="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "nesttalk2026"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🪹 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")

    if settings.TG_BOT_TOKEN:
        from app.services.platform.telegram import tg_adapter
        if tg_adapter:
            await tg_adapter.start()
            logger.info("✅ Telegram Bot 已启动")
    else:
        logger.warning("⚠️ TG_BOT_TOKEN 未配置")

    from app.services.proactive.engine import proactive_engine
    await proactive_engine.start()
    logger.info("✅ 主动交互引擎就绪")

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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ─── API 路由 ─────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@app.get("/api/info")
async def app_info():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "llm_provider": settings.LLM_PROVIDER, "llm_model": settings.LLM_MODEL}

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    if data.get("password") == _read_admin_password():
        return {"success": True, "token": data["password"]}
    return {"success": False, "message": "密码错误"}

# 业务路由
from app.api.characters import router as characters_router
from app.api.worldbooks import router as worldbooks_router
from app.api.presets import router as presets_router
from app.api.chat import router as chat_router
from app.api.backup import router as backup_router
from app.api.memories import router as memories_router
from app.api.admin import router as admin_router

for r in [characters_router, worldbooks_router, presets_router, chat_router, backup_router, memories_router, admin_router]:
    app.include_router(r)


# ─── SPA 静态文件 ─────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    p = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(p) if os.path.isfile(p) else HTMLResponse("<h1>NestTalk</h1>")

@app.get("/{path:path}")
async def serve_static(path: str):
    if path.startswith("api/"):
        return {"error": "not found"}
    fp = os.path.join(STATIC_DIR, path)
    if os.path.isfile(fp):
        return FileResponse(fp)
    ip = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(ip) if os.path.isfile(ip) else HTMLResponse("<h1>NestTalk</h1>")
