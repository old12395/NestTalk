"""角色管理 API"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.core import Character
from app.schemas.models import CharacterCreate, CharacterUpdate, CharacterResponse, APIResponse
from app.services.character.importer import CharacterCardImporter
from loguru import logger

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("", response_model=list[CharacterResponse])
async def list_characters(db: AsyncSession = Depends(get_db)):
    """获取所有角色列表"""
    result = await db.execute(
        select(Character).order_by(Character.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个角色详情"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    return char


@router.post("", response_model=CharacterResponse, status_code=201)
async def create_character(data: CharacterCreate, db: AsyncSession = Depends(get_db)):
    """手动创建角色"""
    char = Character(**data.model_dump())
    db.add(char)
    await db.commit()
    await db.refresh(char)
    logger.info(f"创建角色: {char.name} ({char.id})")
    return char


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新角色"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(char, key, value)

    await db.commit()
    await db.refresh(char)
    logger.info(f"更新角色: {char.name}")
    return char


@router.delete("/{character_id}", response_model=APIResponse)
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)):
    """删除角色"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")

    await db.delete(char)
    await db.commit()
    logger.info(f"删除角色: {char.name}")
    return APIResponse(message=f"角色「{char.name}」已删除")


@router.post("/import", response_model=CharacterResponse, status_code=201)
async def import_character(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    导入角色卡文件。

    支持格式：
    - PNG (Character Card V2/V3)
    - CHARX (Character Card V3)
    - JSON
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查扩展名
    ext = file.filename.lower().split(".")[-1]
    if ext not in ("png", "charx", "json"):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: .{ext}")

    try:
        content = await file.read()
        card_data = CharacterCardImporter.import_from_bytes(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"导入角色卡失败: {e}")
        raise HTTPException(status_code=500, detail="解析角色卡失败")

    # 检查是否已存在同名角色
    existing = await db.execute(
        select(Character).where(Character.name == card_data["name"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"角色「{card_data['name']}」已存在")

    char = Character(**card_data)
    db.add(char)
    await db.commit()
    await db.refresh(char)

    logger.info(f"导入角色卡: {char.name} (spec: {card_data.get('spec')})")
    return char
