"""数据库模型 - 核心表"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Character(Base):
    """角色表 — 兼容酒馆 Character Card V2/V3"""
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    personality: Mapped[str | None] = mapped_column(Text)
    scenario: Mapped[str | None] = mapped_column(Text)
    mes_example: Mapped[str | None] = mapped_column(Text)
    first_mes: Mapped[str | None] = mapped_column(Text)
    alternate_greetings: Mapped[dict | None] = mapped_column(JSON)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    post_history_instructions: Mapped[str | None] = mapped_column(Text)
    creator_notes: Mapped[str | None] = mapped_column(Text)
    creator: Mapped[str | None] = mapped_column(String(255))
    character_version: Mapped[str | None] = mapped_column(String(32))
    spec_version: Mapped[str | None] = mapped_column(String(8), default="3.0")
    spec: Mapped[str | None] = mapped_column(String(32))
    extensions: Mapped[dict | None] = mapped_column(JSON)
    assets: Mapped[list | None] = mapped_column(JSON)
    avatar_url: Mapped[str | None] = mapped_column(Text)  # 头像图片路径
    source: Mapped[list | None] = mapped_column(JSON)
    group_only_greetings: Mapped[list | None] = mapped_column(JSON)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 统计
    total_chats: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    worldbook: Mapped["WorldBook | None"] = relationship(back_populates="character", uselist=False)


class WorldBook(Base):
    """世界书表 - 酒馆 Lorebook 兼容"""
    __tablename__ = "worldbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    character_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("characters.id"), nullable=True)
    entries: Mapped[dict] = mapped_column(JSON, default=dict)  # {"0": {...}, "1": {...}}

    # 设置
    scan_depth: Mapped[int] = mapped_column(Integer, default=100)
    token_budget: Mapped[int] = mapped_column(Integer, default=1024)
    recursive_max_depth: Mapped[int] = mapped_column(Integer, default=3)
    insertion_position: Mapped[str] = mapped_column(String(32), default="before_char")
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    character: Mapped["Character | None"] = relationship(back_populates="worldbook")


class Preset(Base):
    """预设表"""
    __tablename__ = "presets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # 模板
    system_prompt: Mapped[str | None] = mapped_column(Text)
    context_template: Mapped[dict | None] = mapped_column(JSON)  # 上下文编排

    # LLM 参数
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    top_p: Mapped[float] = mapped_column(Float, default=0.9)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    presence_penalty: Mapped[float] = mapped_column(Float, default=0.5)
    frequency_penalty: Mapped[float] = mapped_column(Float, default=0.3)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)  # telegram, qq, wechat
    character_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("characters.id"))
    preset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("presets.id"))
    worldbook_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("worldbooks.id"))

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # 用户画像
    user_profile: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str | None] = mapped_column(String(32))  # text, image, voice, video
    media_url: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryEntry(Base):
    """长期记忆条目（向量存储由 ChromaDB 管理，此表存元数据）"""
    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=1.0)
    source_message_id: Mapped[str | None] = mapped_column(String(36))
    tags: Mapped[list | None] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ScheduledTask(Base):
    """定时任务 / 主动交互"""
    __tablename__ = "scheduled_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32))  # greeting, checkin, festival, custom
    cron_expression: Mapped[str | None] = mapped_column(String(128))
    target_user_id: Mapped[str | None] = mapped_column(String(255))
    character_id: Mapped[str | None] = mapped_column(String(36))
    prompt_template: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelConfig(Base):
    """用户自定义模型配置"""
    __tablename__ = "model_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    config_type: Mapped[str] = mapped_column(String(32))  # llm, vision, image, stt, tts
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    api_key: Mapped[str | None] = mapped_column(String(512))
    base_url: Mapped[str | None] = mapped_column(Text)
    extra_params: Mapped[dict | None] = mapped_column(JSON, default=dict)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
