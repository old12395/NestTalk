"""模型配置 & 平台状态 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.core import ModelConfig, ScheduledTask
from app.schemas.models import APIResponse
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── 模型配置 ────────────────────────────────

@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    """获取所有模型配置"""
    result = await db.execute(select(ModelConfig).order_by(ModelConfig.priority))
    models = result.scalars().all()
    if not models:
        # 返回当前 .env 中的配置作为默认值
        return [{
            "id": "_primary",
            "config_type": "llm",
            "provider": settings.LLM_PROVIDER,
            "model_name": settings.LLM_MODEL,
            "is_primary": True,
            "base_url": settings.LLM_BASE_URL,
        }]
    return models


@router.post("/models")
async def save_model(data: dict, db: AsyncSession = Depends(get_db)):
    """保存模型配置"""
    mc = ModelConfig(**{k: v for k, v in data.items() if hasattr(ModelConfig, k)})
    db.add(mc)
    await db.commit()
    return {"id": mc.id, "message": "模型配置已保存"}


@router.put("/models/{model_id}")
async def update_model(model_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
    mc = result.scalar_one_or_none()
    if not mc:
        raise HTTPException(404, "模型配置不存在")
    for k, v in data.items():
        if hasattr(ModelConfig, k):
            setattr(mc, k, v)
    await db.commit()
    return {"message": "已更新"}


@router.delete("/models/{model_id}")
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
    mc = result.scalar_one_or_none()
    if mc:
        await db.delete(mc)
        await db.commit()
    return {"message": "已删除"}


# ─── 定时任务 / 主动交互 ──────────────────────

@router.get("/tasks")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """获取所有定时任务"""
    result = await db.execute(select(ScheduledTask).order_by(ScheduledTask.created_at))
    tasks = result.scalars().all()
    if not tasks:
        return []
    return tasks


@router.post("/tasks")
async def create_task(data: dict, db: AsyncSession = Depends(get_db)):
    task = ScheduledTask(**{k: v for k, v in data.items() if hasattr(ScheduledTask, k)})
    db.add(task)
    await db.commit()
    return {"id": task.id, "message": "任务已创建"}


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")
    for k, v in data.items():
        if hasattr(ScheduledTask, k):
            setattr(task, k, v)
    await db.commit()
    return {"message": "已更新"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        await db.delete(task)
        await db.commit()
    return {"message": "已删除"}


# ─── 系统状态 ─────────────────────────────────

@router.get("/status")
async def system_status():
    """系统运行状态"""
    import psutil, os
    proc = psutil.Process(os.getpid())
    mem = proc.memory_info()
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "tg_bot": "connected" if settings.TG_BOT_TOKEN else "not configured",
        "memory_mb": round(mem.rss / 1024 / 1024, 1),
        "cpu_percent": proc.cpu_percent(interval=0.1),
        "uptime_seconds": int((__import__('time').time() - proc.create_time())),
    }
