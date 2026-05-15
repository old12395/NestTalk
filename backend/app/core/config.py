"""NestTalk 核心配置"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "NestTalk"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change_me"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/nesttalk.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM 主模型
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"

    # LLM 备用模型
    FALLBACK_PROVIDER: Optional[str] = None
    FALLBACK_API_KEY: Optional[str] = None
    FALLBACK_MODEL: Optional[str] = None
    FALLBACK_BASE_URL: Optional[str] = None

    # 多模态 - 识图
    VISION_PROVIDER: Optional[str] = None
    VISION_API_KEY: Optional[str] = None
    VISION_MODEL: Optional[str] = None
    VISION_BASE_URL: Optional[str] = None

    # 多模态 - 生图
    IMAGE_PROVIDER: Optional[str] = None
    IMAGE_API_KEY: Optional[str] = None
    IMAGE_MODEL: Optional[str] = None
    IMAGE_BASE_URL: Optional[str] = None

    # 多模态 - 语音识别
    STT_PROVIDER: Optional[str] = None
    STT_API_KEY: Optional[str] = None
    STT_MODEL: Optional[str] = None
    STT_BASE_URL: Optional[str] = None

    # 多模态 - 语音合成
    TTS_PROVIDER: Optional[str] = None
    TTS_API_KEY: Optional[str] = None
    TTS_MODEL: Optional[str] = None
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    TTS_BASE_URL: Optional[str] = None

    # Telegram
    TG_BOT_TOKEN: Optional[str] = None

    # 主动交互
    PROACTIVE_ENABLED: bool = True
    PROACTIVE_MAX_PER_HOUR: int = 2
    PROACTIVE_QUIET_START: int = 23  # 静默开始时间（时）
    PROACTIVE_QUIET_END: int = 7    # 静默结束时间（时）

    # 记忆
    MEMORY_MAX_RESULTS: int = 5
    MEMORY_CHUNK_SIZE: int = 512
    MEMORY_OVERLAP: int = 64

    # Token 优化
    MAX_CONTEXT_TOKENS: int = 8192
    HISTORY_MAX_MESSAGES: int = 20
    SUMMARY_THRESHOLD: int = 15  # 超过此轮数触发摘要

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
