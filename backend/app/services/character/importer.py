"""角色卡片导入服务 — 兼容 SillyTavern Character Card V2/V3"""

import json
import base64
import zipfile
import io
from typing import Optional
from PIL import Image
from loguru import logger


class CharacterCardImporter:
    """角色卡导入器，支持 PNG (V2/V3), CHARX (V3), JSON"""

    @staticmethod
    def parse_png_chunks(data: bytes) -> dict:
        """
        解析 PNG 文件中的 tEXt chunks。
        返回 {chunk_name: decoded_text}
        """
        chunks = {}
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("不是有效的 PNG 文件")

        pos = 8
        while pos < len(data):
            length = int.from_bytes(data[pos : pos + 4], "big")
            pos += 4
            chunk_type = data[pos : pos + 4].decode("ascii", errors="ignore")
            pos += 4
            chunk_data = data[pos : pos + length]
            pos += length + 4  # skip CRC

            if chunk_type == "tEXt":
                null_pos = chunk_data.find(b"\x00")
                if null_pos > 0:
                    key = chunk_data[:null_pos].decode("ascii", errors="ignore")
                    value = chunk_data[null_pos + 1 :]
                    chunks[key] = value

            if chunk_type == "IEND":
                break

        return chunks

    @classmethod
    def from_png(cls, file_bytes: bytes) -> dict:
        """从 PNG 文件导入角色卡"""
        chunks = cls.parse_png_chunks(file_bytes)

        card_data = None
        spec = None

        # 优先 V3 (ccv3 chunk)
        if b"ccv3" in chunks or "ccv3" in chunks:
            raw = chunks.get(b"ccv3") or chunks.get("ccv3")
            try:
                decoded = base64.b64decode(raw).decode("utf-8")
                data = json.loads(decoded)
                spec = data.get("spec", "unknown")
                card_data = data.get("data", data)
                logger.info(f"解析 V3 角色卡: {card_data.get('name', 'unknown')}")
            except Exception as e:
                logger.warning(f"V3 解析失败: {e}")

        # 回退 V2 (chara chunk)
        if card_data is None:
            raw = chunks.get(b"chara") or chunks.get("chara")
            if raw:
                try:
                    decoded = base64.b64decode(raw).decode("utf-8")
                    data = json.loads(decoded)
                    spec = "chara_card_v2"
                    card_data = data.get("data", data)
                    logger.info(f"解析 V2 角色卡: {card_data.get('name', 'unknown')}")
                except Exception as e:
                    logger.warning(f"V2 解析失败: {e}")

        # 兜底：尝试从全 JSON 文件解析
        if card_data is None:
            try:
                data = json.loads(file_bytes.decode("utf-8"))
                spec = data.get("spec", "unknown")
                card_data = data.get("data", data)
            except Exception:
                pass

        if card_data is None:
            raise ValueError("无法从文件中解析角色卡数据")

        # 提取头像
        avatar_url = None
        try:
            img = Image.open(io.BytesIO(file_bytes))
            avatar_url = "embedded"  # 实际存储时应保存到本地
        except Exception:
            pass

        return {
            "name": card_data.get("name", "Unknown"),
            "nickname": card_data.get("nickname"),
            "description": card_data.get("description"),
            "personality": card_data.get("personality"),
            "scenario": card_data.get("scenario"),
            "mes_example": card_data.get("mes_example"),
            "first_mes": card_data.get("first_mes"),
            "alternate_greetings": card_data.get("alternate_greetings"),
            "system_prompt": card_data.get("system_prompt"),
            "post_history_instructions": card_data.get("post_history_instructions"),
            "creator_notes": card_data.get("creator_notes"),
            "creator": card_data.get("creator"),
            "character_version": card_data.get("character_version"),
            "spec_version": card_data.get("spec_version", "3.0"),
            "spec": spec,
            "extensions": card_data.get("extensions"),
            "assets": card_data.get("assets"),
            "avatar_url": avatar_url,
            "source": card_data.get("source"),
            "group_only_greetings": card_data.get("group_only_greetings"),
        }

    @classmethod
    def from_charx(cls, file_bytes: bytes) -> dict:
        """从 CHARX (ZIP) 文件导入角色卡"""
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            if "card.json" not in zf.namelist():
                raise ValueError("CHARX 文件中未找到 card.json")

            card_data = json.loads(zf.read("card.json").decode("utf-8"))
            data = card_data.get("data", card_data)

            # TODO: 提取嵌入的资源文件
            assets = {}
            for name in zf.namelist():
                if name != "card.json":
                    assets[name] = zf.read(name)

            logger.info(f"解析 CHARX 角色卡: {data.get('name', 'unknown')}")

        return {
            "name": data.get("name", "Unknown"),
            "nickname": data.get("nickname"),
            "description": data.get("description"),
            "personality": data.get("personality"),
            "scenario": data.get("scenario"),
            "mes_example": data.get("mes_example"),
            "first_mes": data.get("first_mes"),
            "alternate_greetings": data.get("alternate_greetings"),
            "system_prompt": data.get("system_prompt"),
            "post_history_instructions": data.get("post_history_instructions"),
            "creator_notes": data.get("creator_notes"),
            "creator": data.get("creator"),
            "character_version": data.get("character_version"),
            "spec_version": data.get("spec_version", "3.0"),
            "spec": data.get("spec", "chara_card_v3"),
            "extensions": data.get("extensions"),
            "assets": data.get("assets"),
            "source": data.get("source"),
            "group_only_greetings": data.get("group_only_greetings"),
        }

    @classmethod
    def from_json(cls, data: dict) -> dict:
        """从已解析的 JSON 对象构建角色数据"""
        inner = data.get("data", data)
        return {
            "name": inner.get("name", "Unknown"),
            "nickname": inner.get("nickname"),
            "description": inner.get("description"),
            "personality": inner.get("personality"),
            "scenario": inner.get("scenario"),
            "mes_example": inner.get("mes_example"),
            "first_mes": inner.get("first_mes"),
            "alternate_greetings": inner.get("alternate_greetings"),
            "system_prompt": inner.get("system_prompt"),
            "post_history_instructions": inner.get("post_history_instructions"),
            "creator_notes": inner.get("creator_notes"),
            "creator": inner.get("creator"),
            "character_version": inner.get("character_version"),
            "spec_version": inner.get("spec_version", "3.0"),
            "spec": inner.get("spec", "unknown"),
            "extensions": inner.get("extensions"),
            "assets": inner.get("assets"),
            "source": inner.get("source"),
            "group_only_greetings": inner.get("group_only_greetings"),
        }

    @classmethod
    def import_from_bytes(cls, file_bytes: bytes, filename: str = "") -> dict:
        """
        自动检测文件格式并导入角色卡。

        支持格式：
        - .png → Character Card V2/V3 PNG
        - .charx → Character Card V3 CHARX
        - .json → 纯 JSON 角色卡
        """
        ext = filename.lower().split(".")[-1] if filename else ""

        if ext == "charx":
            return cls.from_charx(file_bytes)

        if ext == "png":
            return cls.from_png(file_bytes)

        if ext == "json":
            data = json.loads(file_bytes.decode("utf-8"))
            return cls.from_json(data)

        # 自动检测：先尝试 PNG
        if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return cls.from_png(file_bytes)

        # 尝试 ZIP (CHARX)
        if file_bytes[:4] == b"PK\x03\x04":
            return cls.from_charx(file_bytes)

        # 尝试 JSON
        try:
            data = json.loads(file_bytes.decode("utf-8"))
            return cls.from_json(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError(f"无法识别的文件格式: {filename}")
