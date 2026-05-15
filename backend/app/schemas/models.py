"""Pydantic 数据模型 — 请求/响应 Schema"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ─── 角色 ─────────────────────────────────

class CharacterCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None
    mes_example: Optional[str] = None
    first_mes: Optional[str] = None
    alternate_greetings: Optional[list[str]] = None
    system_prompt: Optional[str] = None
    post_history_instructions: Optional[str] = None
    creator_notes: Optional[str] = None
    creator: Optional[str] = None
    character_version: Optional[str] = None
    spec_version: Optional[str] = "3.0"
    tags: Optional[list[str]] = Field(default_factory=list)


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None
    mes_example: Optional[str] = None
    first_mes: Optional[str] = None
    alternate_greetings: Optional[list[str]] = None
    system_prompt: Optional[str] = None
    post_history_instructions: Optional[str] = None
    creator_notes: Optional[str] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class CharacterResponse(BaseModel):
    id: str
    name: str
    nickname: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None
    mes_example: Optional[str] = None
    first_mes: Optional[str] = None
    system_prompt: Optional[str] = None
    post_history_instructions: Optional[str] = None
    creator_notes: Optional[str] = None
    creator: Optional[str] = None
    character_version: Optional[str] = None
    spec_version: Optional[str] = None
    tags: Optional[list[str]] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    total_chats: int = 0
    total_messages: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── 世界书 ─────────────────────────────────

class WorldBookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    character_id: Optional[str] = None
    entries: dict = Field(default_factory=dict)
    is_global: bool = False


class WorldBookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entries: Optional[dict] = None
    is_global: Optional[bool] = None
    scan_depth: Optional[int] = None
    token_budget: Optional[int] = None


class WorldBookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    character_id: Optional[str] = None
    entries: dict
    scan_depth: int = 100
    token_budget: int = 1024
    is_global: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── 预设 ─────────────────────────────────

class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    context_template: Optional[dict] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    presence_penalty: float = 0.5
    frequency_penalty: float = 0.3


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    context_template: Optional[dict] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None


class PresetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    context_template: Optional[dict] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    presence_penalty: float = 0.5
    frequency_penalty: float = 0.3
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── 对话 ─────────────────────────────────

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    platform: str
    character_id: Optional[str] = None
    preset_id: Optional[str] = None
    is_active: bool = True
    total_messages: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    created_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    tokens_used: int = 0
    cost: float = 0.0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── 通用 ─────────────────────────────────

class APIResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Any = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
