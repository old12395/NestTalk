"""对话 API — 聊天交互端点"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.chat.engine import chat_engine
from loguru import logger

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    character_id: Optional[str] = None
    character_name: Optional[str] = "小栖"
    user_name: Optional[str] = "用户"
    history: Optional[list[dict]] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None


class ChatResponse(BaseModel):
    content: str
    tokens: int = 0
    model: str = ""


@router.post("/send", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    """发送消息并获取回复"""
    character = {
        "name": req.character_name or "小栖",
        "personality": req.personality or "温暖、善解人意的AI陪伴者",
        "scenario": req.scenario or "在手机里陪伴用户聊天",
        "description": "你是用户的AI陪伴者，温柔体贴，随时陪在ta身边",
        "mes_example": None,
    }

    try:
        result = await chat_engine.chat(
            character=character,
            message=req.message,
            history=req.history,
            user_name=req.user_name,
        )

        return ChatResponse(
            content=result.get("content", ""),
            tokens=result.get("tokens", 0),
            model=result.get("model", ""),
        )
    except Exception as e:
        logger.error(f"聊天失败: {e}")
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")
