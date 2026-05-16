"""系统配置 & 服务管理 API — 运行时改配置，无需手动编辑 .env"""

import os, subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── 运行时配置模型 ──────────────────────────

class RuntimeConfig(BaseModel):
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    tg_bot_token: str = ""
    vision_provider: Optional[str] = None
    vision_api_key: Optional[str] = None
    vision_model: Optional[str] = None
    image_provider: Optional[str] = None
    image_api_key: Optional[str] = None
    image_model: Optional[str] = None
    stt_provider: Optional[str] = None
    stt_api_key: Optional[str] = None
    stt_model: Optional[str] = None
    tts_provider: Optional[str] = "edge_tts"
    tts_voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    admin_password: str = "nesttalk2026"
    proactive_enabled: bool = True
    proactive_max_per_hour: int = 2
    proactive_quiet_start: int = 23
    proactive_quiet_end: int = 7


ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")


def _read_env() -> dict:
    """读取 .env 文件"""
    config = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    return config


def _write_env(config: dict):
    """写入 .env 文件"""
    with open(ENV_PATH, "w") as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")


# ─── 获取当前配置 ────────────────────────────

@router.get("/config")
async def get_config():
    """获取当前运行时配置"""
    config = _read_env()
    return {
        "llm_provider": config.get("LLM_PROVIDER", settings.LLM_PROVIDER),
        "llm_model": config.get("LLM_MODEL", settings.LLM_MODEL),
        "llm_base_url": config.get("LLM_BASE_URL", settings.LLM_BASE_URL),
        "llm_api_key": _mask_key(config.get("LLM_API_KEY", "")),
        "tg_bot_token": _mask_key(config.get("TG_BOT_TOKEN", "")),
        "vision_provider": config.get("VISION_PROVIDER", ""),
        "vision_model": config.get("VISION_MODEL", ""),
        "vision_api_key": _mask_key(config.get("VISION_API_KEY", "")),
        "image_provider": config.get("IMAGE_PROVIDER", ""),
        "image_model": config.get("IMAGE_MODEL", ""),
        "image_api_key": _mask_key(config.get("IMAGE_API_KEY", "")),
        "stt_provider": config.get("STT_PROVIDER", ""),
        "stt_model": config.get("STT_MODEL", ""),
        "stt_api_key": _mask_key(config.get("STT_API_KEY", "")),
        "tts_provider": config.get("TTS_PROVIDER", "edge_tts"),
        "tts_voice": config.get("TTS_VOICE", "zh-CN-XiaoxiaoNeural"),
        "admin_password": config.get("ADMIN_PASSWORD", "nesttalk2026"),
        "proactive_enabled": config.get("PROACTIVE_ENABLED", "true"),
        "proactive_max_per_hour": config.get("PROACTIVE_MAX_PER_HOUR", "2"),
        "proactive_quiet_start": config.get("PROACTIVE_QUIET_START", "23"),
        "proactive_quiet_end": config.get("PROACTIVE_QUIET_END", "7"),
        "fallback_provider": config.get("FALLBACK_PROVIDER", ""),
        "fallback_model": config.get("FALLBACK_MODEL", ""),
        "app_version": settings.APP_VERSION,
        "env_path": ENV_PATH,
    }


# ─── 保存配置 ─────────────────────────────────

@router.post("/config")
async def save_config(data: RuntimeConfig):
    """保存运行时配置到 .env 文件"""
    config = _read_env()

    # 更新 LLM 配置
    if data.llm_provider:
        config["LLM_PROVIDER"] = data.llm_provider
    if data.llm_model:
        config["LLM_MODEL"] = data.llm_model
    if data.llm_base_url:
        config["LLM_BASE_URL"] = data.llm_base_url
    if data.llm_api_key and data.llm_api_key != "***MASKED***":
        config["LLM_API_KEY"] = data.llm_api_key

    # TG Bot
    if data.tg_bot_token and data.tg_bot_token != "***MASKED***":
        config["TG_BOT_TOKEN"] = data.tg_bot_token

    # 多模态
    for key in ["vision", "image", "stt", "tts"]:
        provider_key = f"{key.upper()}_PROVIDER"
        api_key_key = f"{key.upper()}_API_KEY"
        model_key = f"{key.upper()}_MODEL"

        provider_val = getattr(data, f"{key}_provider", None)
        api_key_val = getattr(data, f"{key}_api_key", None)
        model_val = getattr(data, f"{key}_model", None)

        if provider_val:
            config[provider_key] = provider_val
        if api_key_val and api_key_val != "***MASKED***":
            config[api_key_key] = api_key_val
        if model_val:
            config[model_key] = model_val

    # TTS voice
    if data.tts_voice:
        config["TTS_VOICE"] = data.tts_voice

    # 主动交互
    config["PROACTIVE_ENABLED"] = str(data.proactive_enabled).lower()
    config["PROACTIVE_MAX_PER_HOUR"] = str(data.proactive_max_per_hour)
    config["PROACTIVE_QUIET_START"] = str(data.proactive_quiet_start)
    config["PROACTIVE_QUIET_END"] = str(data.proactive_quiet_end)

    # Admin password
    if data.admin_password:
        config["ADMIN_PASSWORD"] = data.admin_password

    _write_env(config)
    logger.info("✅ 配置已写入 .env")
    return {"message": "配置已保存，需要重启服务才能生效", "need_restart": True}


# ─── 服务重启 ─────────────────────────────────

@router.post("/restart")
async def restart_service():
    """重启 NestTalk 服务（systemd）"""
    try:
        result = subprocess.run(
            ["systemctl", "restart", "nesttalk"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            logger.info("🔄 服务重启已触发")
            return {"message": "服务正在重启，约 5 秒后恢复"}
        else:
            logger.error(f"重启失败: {result.stderr}")
            raise HTTPException(500, f"重启失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "重启超时")
    except FileNotFoundError:
        raise HTTPException(500, "systemctl 不可用，请手动重启")


# ─── 系统状态 ─────────────────────────────────

@router.get("/status")
async def system_status():
    """系统运行状态"""
    import psutil, time, os
    proc = psutil.Process(os.getpid())
    mem = proc.memory_info()
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "tg_bot": "connected" if settings.TG_BOT_TOKEN else "not configured",
        "memory_mb": round(mem.rss / 1024 / 1024, 1),
        "cpu_percent": round(proc.cpu_percent(interval=0.1), 1),
        "uptime_seconds": int(time.time() - proc.create_time()),
    }


def _mask_key(key: str) -> str:
    """脱敏显示 API Key"""
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return key[:3] + "***" + key[-4:]
