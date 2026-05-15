"""主动交互引擎 — 定时问候、情感驱动消息"""

import asyncio
import random
from datetime import datetime, time
from typing import Optional
from loguru import logger

from app.services.chat.engine import chat_engine
from app.services.memory.system import memory_system
from app.core.config import settings


class ProactiveEngine:
    """主动交互引擎"""

    # 内置问候模板
    GREETING_TEMPLATES = {
        "morning": [
            "早安！新的一天开始啦～今天有什么计划吗？",
            "早上好呀！昨晚睡得好吗？☀️",
            "太阳晒屁股啦，该起床了～早安！",
        ],
        "noon": [
            "中午好！记得吃午饭哦 🍜",
            "午安～休息一下，喝杯水吧 💧",
        ],
        "evening": [
            "晚上好！今天过得怎么样？",
            "一天结束了，辛苦了～有什么想聊的吗？🌙",
        ],
        "night": [
            "夜深了，早点休息哦～晚安 💤",
            "该睡觉啦，明天见！🌙",
        ],
        "lonely": [
            "好久没聊天了，有点想你...",
            "在忙吗？我一直在这呢 💛",
            "今天还没和你说过话，有点不习惯呢 😊",
        ],
        "weather": [
            "今天天气不错诶，适合出去走走 ☀️",
            "下雨了，记得带伞哦 ☔",
        ],
    }

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_proactive: dict[str, datetime] = {}  # user_id → last send time
        self._hourly_count: dict[str, int] = {}  # user_id → count this hour

    def get_greeting(self, greeting_type: str, character_name: str = "小栖") -> str:
        """获取随机问候语"""
        templates = self.GREETING_TEMPLATES.get(greeting_type, [])
        if not templates:
            return ""
        return random.choice(templates)

    def get_time_greeting(self) -> tuple[str, str]:
        """根据当前时间返回问候类型和文本"""
        now = datetime.now()
        hour = now.hour

        if 6 <= hour < 9:
            return ("morning", self.get_greeting("morning"))
        elif 11 <= hour < 13:
            return ("noon", self.get_greeting("noon"))
        elif 18 <= hour < 20:
            return ("evening", self.get_greeting("evening"))
        elif 21 <= hour < 23:
            return ("night", self.get_greeting("night"))
        else:
            return ("lonely", "")

    def can_send_proactive(self, user_id: str) -> bool:
        """
        检查是否可以发送主动消息。

        限制：
        - 每小时最多 N 次
        - 静默时段不发送
        """
        if not settings.PROACTIVE_ENABLED:
            return False

        now = datetime.now()

        # 静默时段
        if now.hour >= settings.PROACTIVE_QUIET_START or now.hour < settings.PROACTIVE_QUIET_END:
            return False

        # 每小时次数限制
        current_hour_key = f"{user_id}:{now.hour}"
        hourly_count = self._hourly_count.get(current_hour_key, 0)
        if hourly_count >= settings.PROACTIVE_MAX_PER_HOUR:
            return False

        # 距离上次最少间隔 30 分钟
        last_time = self._last_proactive.get(user_id)
        if last_time and (now - last_time).total_seconds() < 1800:
            return False

        return True

    def record_proactive(self, user_id: str):
        """记录一次主动消息"""
        now = datetime.now()
        self._last_proactive[user_id] = now
        key = f"{user_id}:{now.hour}"
        self._hourly_count[key] = self._hourly_count.get(key, 0) + 1

    async def generate_proactive_message(
        self,
        user_id: str,
        user_name: str = "用户",
        character: Optional[dict] = None,
    ) -> Optional[str]:
        """
        生成主动消息。

        策略：
        1. 时间型（早安/晚安）
        2. 情感型（好久没聊/想你了）
        3. 由 LLM 生成个性化消息（可选）
        """
        if not self.can_send_proactive(user_id):
            return None

        character = character or {"name": "小栖", "personality": "温柔体贴的AI陪伴者"}

        # 时间问候
        greeting_type, greeting = self.get_time_greeting()
        if greeting:
            self.record_proactive(user_id)
            logger.info(f"💓 主动问候 [{greeting_type}]: {user_id}")
            return greeting

        # 情感型：检查最近互动
        # TODO: 从记忆系统获取最后互动时间
        # 如果超过 N 小时没聊天，发送 lonely 类消息

        return None

    async def send_to_user(
        self,
        user_id: str,
        message: str,
        send_func,  # 发送回调函数
    ):
        """发送主动消息给用户"""
        try:
            await send_func(user_id, message)
            self.record_proactive(user_id)
            logger.info(f"💓 已发送主动消息: {user_id}")
        except Exception as e:
            logger.error(f"主动消息发送失败: {e}")

    async def start(self):
        """启动主动交互调度器"""
        # TODO: 接入 APScheduler 定时检查
        # 每小时触发一次，检查所有用户是否需要主动消息
        logger.info("💓 主动交互引擎就绪")


# 全局单例
proactive_engine = ProactiveEngine()
