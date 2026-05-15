"""预设管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.core import Preset
from app.schemas.models import PresetCreate, PresetUpdate, PresetResponse, APIResponse
from loguru import logger

router = APIRouter(prefix="/api/presets", tags=["presets"])


@router.get("", response_model=list[PresetResponse])
async def list_presets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Preset).order_by(Preset.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Preset).where(Preset.id == preset_id)
    )
    preset = result.scalar_one_or_none()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")
    return preset


@router.post("", response_model=PresetResponse, status_code=201)
async def create_preset(data: PresetCreate, db: AsyncSession = Depends(get_db)):
    preset = Preset(**data.model_dump())
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    logger.info(f"创建预设: {preset.name}")
    return preset


@router.put("/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: str, data: PresetUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Preset).where(Preset.id == preset_id))
    preset = result.scalar_one_or_none()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(preset, key, value)

    await db.commit()
    await db.refresh(preset)
    return preset


@router.delete("/{preset_id}", response_model=APIResponse)
async def delete_preset(preset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Preset).where(Preset.id == preset_id))
    preset = result.scalar_one_or_none()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    await db.delete(preset)
    await db.commit()
    return APIResponse(message=f"预设「{preset.name}」已删除")
