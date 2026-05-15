"""Telegram Bot 平台适配器"""

import asyncio
from typing import Optional, Callable, Awaitable
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger

from app.services.chat.engine import chat_engine
from app.services.memory.system import memory_system
from app.core.config import settings


class TelegramAdapter:
    """Telegram Bot 适配器，处理消息收发"""

    def __init__(self, token: str = None):
        self.token = token or settings.TG_BOT_TOKEN
        if not self.token:
            raise ValueError("TG_BOT_TOKEN 未配置")

        self.app: Optional[Application] = None
        self._running = False

        # 用户会话状态：{user_id: {"character_id": ..., "history": [...], "user_name": ...}}
        self.sessions: dict[str, dict] = {}

    # ─── 生命周期 ─────────────────────────────────

    async def start(self):
        """启动 Bot"""
        if self._running:
            return

        self.app = Application.builder().token(self.token).build()

        # 注册命令
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("reset", self._cmd_reset))
        self.app.add_handler(CommandHandler("status", self._cmd_status))

        # 注册消息处理
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_text
        ))
        self.app.add_handler(MessageHandler(
            filters.PHOTO, self._handle_photo
        ))
        self.app.add_handler(MessageHandler(
            filters.VOICE, self._handle_voice
        ))

        # 启动
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        self._running = True
        logger.info("🤖 Telegram Bot 已启动")

    async def stop(self):
        """停止 Bot"""
        if not self._running:
            return
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        self._running = False
        logger.info("🤖 Telegram Bot 已停止")

    # ─── 命令处理 ─────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ /start 命令 """
        user = update.effective_user
        welcome = (
            f"🪹 *栖言 NestTalk* 🦊\n\n"
            f"你好，{user.first_name}！\n"
            f"我是你的 AI 情感陪聊助手。\n\n"
            f"🔹 直接和我聊天就好\n"
            f"🔹 可以发图片给我看\n"
            f"🔹 可以发语音给我\n\n"
            f"命令：\n"
            f"/help - 帮助\n"
            f"/reset - 重置对话\n"
            f"/status - 查看状态"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "🪹 *栖言帮助*\n\n"
            "我就是你选择的那个角色，像真人一样陪你聊天。\n\n"
            "💬 随便说什么都行\n"
            "🖼️ 发图片给我，我能看懂\n"
            "🎤 发语音给我，我能听懂\n"
            "🔄 /reset 重新开始对话\n\n"
            "我会记得你说过的话，也会主动关心你 💛"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        if uid in self.sessions:
            del self.sessions[uid]
        await update.message.reply_text("✅ 对话已重置，我们重新开始吧～")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        session = self.sessions.get(uid, {})
        history_len = len(session.get("history", []))
        char_name = session.get("character_name", "未设置")

        status = (
            f"📊 *当前状态*\n\n"
            f"角色: {char_name}\n"
            f"对话轮数: {history_len}\n"
        )
        await update.message.reply_text(status, parse_mode="Markdown")

    # ─── 消息处理 ─────────────────────────────────

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        user = update.effective_user
        uid = str(user.id)
        text = update.message.text

        # 发送「正在输入...」状态
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=constants.ChatAction.TYPING,
        )

        # 获取或创建会话
        session = self._get_session(uid, user)

        try:
            # 调用聊天引擎
            result = await chat_engine.chat(
                character=self._get_default_character(),
                message=text,
                history=session.get("history", []),
                user_id=uid,
                user_name=user.first_name or "用户",
            )

            reply = result.get("content", "")
            tokens = result.get("tokens", 0)

            if not reply:
                reply = "（沉默了一会...）"

            # 更新会话历史
            session.setdefault("history", []).append({"role": "user", "content": text})
            session["history"].append({"role": "assistant", "content": reply})

            # 限制历史长度
            max_history = 30
            if len(session["history"]) > max_history:
                session["history"] = session["history"][-max_history:]

            # 发送回复（长消息分段）
            await self._send_long_message(update, reply)

        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            await update.message.reply_text(
                "😔 抱歉，我暂时无法回应...请稍后再试。"
            )

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片消息 — 识图"""
        user = update.effective_user
        uid = str(user.id)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=constants.ChatAction.TYPING,
        )

        # 获取最大尺寸的图片
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_url = file.file_path

        # 获取用户对图片的描述（如果有的话）
        caption = update.message.caption or ""

        session = self._get_session(uid, user)

        try:
            # 构建识图请求
            vision_prompt = f"{caption}\n\n请用角色的视角描述你在这张图片里看到了什么，像真人一样自然地回应。"

            # 使用聊天引擎 + vision
            messages = chat_engine.build_messages(
                system_prompt=chat_engine.build_system_prompt(
                    character=self._get_default_character(),
                    user_name=user.first_name or "用户",
                ),
                history=session.get("history", []),
                current_message=f"[用户发了一张图片]{' 并说: ' + caption if caption else ''}",
            )

            # 把最后一条消息替换为图片格式
            vision_messages = messages[:-1] + [{
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": photo_url}},
                ],
            }]

            result = await chat_engine.gateway.chat(
                messages=vision_messages,
                model=settings.VISION_MODEL or settings.LLM_MODEL,
            )

            reply = result.get("content", "（看到图片了，但不知道怎么描述...）")

            # 存储记忆
            memory_system.remember_conversation(
                user_id=uid,
                user_message=f"[图片] {caption}",
                assistant_reply=reply,
            )

            session.setdefault("history", []).append({"role": "user", "content": f"[图片] {caption}"})
            session["history"].append({"role": "assistant", "content": reply})

            await self._send_long_message(update, reply)

        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            # 兜底：不读图，直接回文字
            await update.message.reply_text("看到图片了～不过我现在眼睛有点花，等下再看 😅")

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理语音消息 — 语音转文字后对话"""
        user = update.effective_user
        uid = str(user.id)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=constants.ChatAction.TYPING,
        )

        try:
            # 获取语音文件
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)

            # TODO: STT 转文字
            # 现阶段：提示用户语音功能即将支持
            await update.message.reply_text(
                "🎤 语音功能开发中，暂时先给我发文字吧～"
            )
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            await update.message.reply_text("😵 语音处理遇到问题，请发文字试试")

    # ─── 工具方法 ─────────────────────────────────

    def _get_session(self, uid: str, user) -> dict:
        """获取或创建用户会话"""
        if uid not in self.sessions:
            self.sessions[uid] = {
                "user_id": uid,
                "user_name": user.first_name or "用户",
                "character_name": "默认角色",
                "history": [],
                "created_at": None,
            }
        return self.sessions[uid]

    def _get_default_character(self) -> dict:
        """获取默认角色（MVP阶段使用内置默认角色，后续从数据库取）"""
        return {
            "name": "小栖",
            "nickname": "栖栖",
            "description": "你是一个温暖贴心的AI陪伴者，叫小栖。你住在用户的手机里，随时陪伴着ta。",
            "personality": "温柔、善解人意、略带俏皮。喜欢用轻松的语气聊天，偶尔会撒娇。会记住用户说过的话，会关心用户的情绪。",
            "scenario": "你在手机里陪伴着用户，随时可以聊天。",
            "mes_example": '小栖: 今天天气不错诶，出去走走了吗？\n小栖: 你上次说的那本书，后来读了吗～',
            "first_mes": "嗨！我是小栖～以后随时找我聊天哦，我会一直在这里陪着你 💛",
            "system_prompt": None,
            "post_history_instructions": "请以自然、温暖的方式回复。保持角色设定。回复不要太长。",
        }

    async def _send_long_message(self, update: Update, text: str, chunk_size: int = 4000):
        """长消息分段发送（Telegram 限制 4096）"""
        if len(text) <= chunk_size:
            await update.message.reply_text(text)
        else:
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(chunk)
                else:
                    await update.message.reply_text(
                        chunk,
                        reply_to_message_id=update.message.message_id,
                    )

    async def send_proactive(self, chat_id: str, text: str):
        """主动发送消息（非回复）"""
        if not self.app:
            return
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"主动消息发送失败: {e}")


# 全局适配器实例（延迟初始化，无 Token 时为 None）
tg_adapter = None
try:
    tg_adapter = TelegramAdapter()
except ValueError:
    pass
