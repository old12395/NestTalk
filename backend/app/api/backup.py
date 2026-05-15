"""备份 API — 导出/导入"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.core import Character, WorldBook, Preset, ModelConfig, ScheduledTask
from app.services.backup.manager import BackupManager, CURRENT_BACKUP_VERSION
from app.schemas.models import APIResponse
from loguru import logger
import json

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
async def export_backup(db: AsyncSession = Depends(get_db)):
    """导出所有数据为备份文件"""
    # 收集数据
    chars = await db.execute(select(Character))
    characters = [_row_to_dict(c) for c in chars.scalars().all()]

    wbs = await db.execute(select(WorldBook))
    world_books = [_row_to_dict(w) for w in wbs.scalars().all()]

    ps = await db.execute(select(Preset))
    presets = [_row_to_dict(p) for p in ps.scalars().all()]

    # 模型配置
    mcs = await db.execute(select(ModelConfig))
    model_configs = [_row_to_dict(m) for m in mcs.scalars().all()]

    # 定时任务
    tasks = await db.execute(select(ScheduledTask))
    scheduled_tasks = [_row_to_dict(t) for t in tasks.scalars().all()]

    backup = BackupManager.export_backup(
        characters=characters,
        world_books=world_books,
        presets=presets,
        model_configs=model_configs,
        platform_configs={},
        system_settings={},
        scheduled_tasks=scheduled_tasks,
    )

    logger.info(f"导出备份: {len(characters)} 角色, {len(world_books)} 世界书, {len(presets)} 预设")
    return JSONResponse(content=backup)


@router.post("/import", response_model=APIResponse)
async def import_backup(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """导入备份文件"""
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="请上传 .json 备份文件")

    try:
        content = await file.read()
        backup = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")

    try:
        result = BackupManager.import_backup(backup, CURRENT_BACKUP_VERSION)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    data = result["data"]
    warnings = result["warnings"]

    # 导入角色
    char_count = 0
    for char_data in data.get("characters", []):
        existing = await db.execute(
            select(Character).where(Character.name == char_data.get("name"))
        )
        if not existing.scalar_one_or_none():
            db.add(Character(**{k: v for k, v in char_data.items() if k != "id" and hasattr(Character, k)}))
            char_count += 1

    # 导入世界书
    wb_count = 0
    for wb_data in data.get("world_books", []):
        existing = await db.execute(
            select(WorldBook).where(WorldBook.name == wb_data.get("name"))
        )
        if not existing.scalar_one_or_none():
            db.add(WorldBook(**{k: v for k, v in wb_data.items() if k != "id" and hasattr(WorldBook, k)}))
            wb_count += 1

    # 导入预设
    preset_count = 0
    for preset_data in data.get("presets", []):
        existing = await db.execute(
            select(Preset).where(Preset.name == preset_data.get("name"))
        )
        if not existing.scalar_one_or_none():
            db.add(Preset(**{k: v for k, v in preset_data.items() if k != "id" and hasattr(Preset, k)}))
            preset_count += 1

    await db.commit()

    logger.info(f"导入备份: {char_count} 角色, {wb_count} 世界书, {preset_count} 预设")
    return APIResponse(
        message=f"导入完成: {char_count} 角色, {wb_count} 世界书, {preset_count} 预设",
        data={"warnings": warnings},
    )


def _row_to_dict(row) -> dict:
    """将 SQLAlchemy 模型转为字典"""
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif isinstance(value, dict) or isinstance(value, list):
            value = value
        result[column.name] = value
    return result
