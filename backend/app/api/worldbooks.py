"""世界书管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.core import WorldBook
from app.schemas.models import WorldBookCreate, WorldBookUpdate, WorldBookResponse, APIResponse
from loguru import logger

router = APIRouter(prefix="/api/worldbooks", tags=["worldbooks"])


@router.get("", response_model=list[WorldBookResponse])
async def list_worldbooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorldBook).order_by(WorldBook.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{wb_id}", response_model=WorldBookResponse)
async def get_worldbook(wb_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorldBook).where(WorldBook.id == wb_id)
    )
    wb = result.scalar_one_or_none()
    if not wb:
        raise HTTPException(status_code=404, detail="世界书不存在")
    return wb


@router.post("", response_model=WorldBookResponse, status_code=201)
async def create_worldbook(data: WorldBookCreate, db: AsyncSession = Depends(get_db)):
    wb = WorldBook(**data.model_dump())
    db.add(wb)
    await db.commit()
    await db.refresh(wb)
    logger.info(f"创建世界书: {wb.name}")
    return wb


@router.put("/{wb_id}", response_model=WorldBookResponse)
async def update_worldbook(wb_id: str, data: WorldBookUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorldBook).where(WorldBook.id == wb_id))
    wb = result.scalar_one_or_none()
    if not wb:
        raise HTTPException(status_code=404, detail="世界书不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(wb, key, value)

    await db.commit()
    await db.refresh(wb)
    return wb


@router.delete("/{wb_id}", response_model=APIResponse)
async def delete_worldbook(wb_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorldBook).where(WorldBook.id == wb_id))
    wb = result.scalar_one_or_none()
    if not wb:
        raise HTTPException(status_code=404, detail="世界书不存在")

    await db.delete(wb)
    await db.commit()
    return APIResponse(message=f"世界书「{wb.name}」已删除")
