"""记忆管理 API"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.services.memory.system import memory_system
from app.schemas.models import APIResponse
from loguru import logger

router = APIRouter(prefix="/api/memories", tags=["memories"])


class MemorySearchRequest(BaseModel):
    user_id: str
    query: str
    top_k: int = 10


@router.get("/{user_id}")
async def list_memories(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """获取用户的记忆列表"""
    try:
        profile = memory_system.extract_profile(user_id)
        # 用空查询获取所有记忆
        memories = memory_system.recall(user_id, query="", top_k=limit, min_importance=0)
        return {
            "user_id": user_id,
            "total": profile.get("memory_count", 0),
            "items": [
                {
                    "content": m["content"],
                    "importance": m["importance"],
                    "relevance": m["relevance"],
                    "tags": m.get("tags", []),
                    "created_at": m.get("created_at", ""),
                }
                for m in memories
            ],
        }
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_memories(req: MemorySearchRequest):
    """搜索用户记忆"""
    try:
        memories = memory_system.recall(
            user_id=req.user_id,
            query=req.query,
            top_k=req.top_k,
        )
        return {
            "query": req.query,
            "results": [
                {
                    "content": m["content"],
                    "importance": m["importance"],
                    "relevance": m["relevance"],
                    "tags": m.get("tags", []),
                }
                for m in memories
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", response_model=APIResponse)
async def clear_memories(user_id: str):
    """清空用户记忆"""
    try:
        memory_system.clear_user_memories(user_id)
        return APIResponse(message=f"已清空用户 {user_id} 的记忆")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decay/{user_id}", response_model=APIResponse)
async def decay_memories(user_id: str, days: int = Query(default=30)):
    """执行记忆衰减"""
    try:
        memory_system.decay_memories(user_id, days_threshold=days)
        return APIResponse(message=f"已完成记忆衰减处理 (阈值 {days} 天)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
