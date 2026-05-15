"""数据备份与迁移服务 — 版本化导出/导入，向前向后兼容"""

import json
import hashlib
from datetime import datetime
from typing import Any, Optional
from loguru import logger

# 当前备份格式版本
CURRENT_BACKUP_VERSION = "1.0.0"


class BackupManager:
    """管理数据备份、导出、导入和版本迁移"""

    @staticmethod
    def export_backup(
        characters: list[dict],
        world_books: list[dict],
        presets: list[dict],
        model_configs: list[dict],
        platform_configs: dict,
        system_settings: dict,
        scheduled_tasks: list[dict],
        memories: Optional[list[dict]] = None,
    ) -> dict:
        """
        生成格式化的备份数据包。

        Args:
            characters: 角色列表
            world_books: 世界书列表
            presets: 预设列表
            model_configs: 模型配置列表（自动脱敏 API Key）
            platform_configs: 平台配置（自动脱敏 Token）
            system_settings: 系统设置
            scheduled_tasks: 定时任务列表
            memories: 长期记忆（可选，因为数据量大）

        Returns:
            完整的备份数据包字典
        """
        # 脱敏处理
        safe_model_configs = BackupManager._redact_api_keys(model_configs)
        safe_platform_configs = BackupManager._redact_tokens(platform_configs)

        backup = {
            "format": "nesttalk_backup_v1",
            "version": CURRENT_BACKUP_VERSION,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "app_version": "0.1.0",  # TODO: 从 settings 读取
            "data": {
                "characters": characters,
                "world_books": world_books,
                "presets": presets,
                "model_configs": safe_model_configs,
                "platform_configs": safe_platform_configs,
                "system_settings": system_settings,
                "scheduled_tasks": scheduled_tasks,
                "memories": memories or [],
            },
        }

        # 计算校验和
        data_str = json.dumps(backup["data"], sort_keys=True, ensure_ascii=False)
        backup["checksum"] = hashlib.sha256(data_str.encode()).hexdigest()

        return backup

    @staticmethod
    def validate_backup(backup: dict) -> bool:
        """验证备份文件完整性"""
        if "checksum" not in backup or "data" not in backup:
            return False

        data_str = json.dumps(backup["data"], sort_keys=True, ensure_ascii=False)
        expected = hashlib.sha256(data_str.encode()).hexdigest()
        return backup["checksum"] == expected

    @staticmethod
    def import_backup(backup: dict, current_version: str) -> dict:
        """
        导入备份数据，自动处理版本兼容。

        Returns:
            {"data": {...}, "warnings": [...], "migrated": bool}
        """
        warnings = []
        backup_version = backup.get("version", "unknown")

        # 版本检查
        if not BackupManager.validate_backup(backup):
            raise ValueError("备份文件校验失败，文件可能已损坏")

        data = backup.get("data", {})

        # 旧版 → 新版：自动迁移
        if BackupManager._compare_versions(backup_version, current_version) < 0:
            data = BackupManager._migrate_up(data, backup_version, current_version)
            warnings.append(f"备份文件已从 v{backup_version} 自动迁移到 v{current_version}")

        # 新版 → 旧版：警告 + 尽力导入
        elif BackupManager._compare_versions(backup_version, current_version) > 0:
            warnings.append(
                f"⚠️ 备份文件版本 (v{backup_version}) 高于当前系统版本 (v{current_version})，"
                f"部分功能可能不受支持。核心数据（角色、世界书、预设）将正常导入。"
            )
            data = BackupManager._migrate_down(data, backup_version, current_version)

        return {
            "data": data,
            "warnings": warnings,
            "migrated": backup_version != current_version,
        }

    @staticmethod
    def _migrate_up(data: dict, from_version: str, to_version: str) -> dict:
        """从旧版本迁移到新版本"""
        # 目前只有一个版本，后续在此添加迁移逻辑
        # 示例：v1 → v2: data["model_configs"] = transform_model_configs_v1_to_v2(...)
        logger.info(f"数据迁移: v{from_version} → v{to_version}")
        return data

    @staticmethod
    def _migrate_down(data: dict, from_version: str, to_version: str) -> dict:
        """从新版本迁移到旧版本（尽力而为）"""
        # 移除旧版不支持的字段
        # 目前暂不处理，等有多个版本后再细化
        logger.warning(f"数据降级: v{from_version} → v{to_version}，部分字段可能丢失")
        return data

    @staticmethod
    def _redact_api_keys(configs: list[dict]) -> list[dict]:
        """脱敏 API Key"""
        result = []
        for c in configs:
            safe = dict(c)
            if "api_key" in safe and safe["api_key"]:
                safe["api_key"] = "***REDACTED***"
            result.append(safe)
        return result

    @staticmethod
    def _redact_tokens(configs: dict) -> dict:
        """脱敏平台 Token"""
        import copy

        safe = copy.deepcopy(configs)
        sensitive_keys = ["bot_token", "token", "access_token", "api_key", "secret"]
        for key, value in safe.items():
            if isinstance(value, dict):
                for sk in sensitive_keys:
                    if sk in value and value[sk]:
                        value[sk] = "***REDACTED***"
        return safe

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """比较版本号：-1=旧, 0=等, 1=新"""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            for a, b in zip(parts1, parts2):
                if a < b:
                    return -1
                if a > b:
                    return 1
            return 0
        except (ValueError, AttributeError):
            return -1 if v1 < v2 else (1 if v1 > v2 else 0)
