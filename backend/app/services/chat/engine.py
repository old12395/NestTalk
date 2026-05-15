"""聊天核心引擎 — 对话编排、上下文拼接、LLM 调用"""

from typing import Optional, AsyncIterator
from loguru import logger
from app.services.llm_gateway.gateway import llm_gateway


class ChatEngine:
    """对话引擎：拼装上下文 → 调用 LLM → 返回回复"""

    # 默认预设模板
    DEFAULT_SYSTEM_PROMPT = """你是 {{char}}，现在正在和 {{user}} 对话。

{{#if personality}}
你的性格特点：{{personality}}
{{/if}}

{{#if scenario}}
当前场景：{{scenario}}
{{/if}}

{{#if description}}
关于你：{{description}}
{{/if}}

{{#if mes_example}}
对话风格参考：
{{mes_example}}
{{/if}}

{{#if world_book_entries}}
【当前相关背景信息】
{{world_book_entries}}
{{/if}}

{{#if memories}}
【你记得关于 {{user}} 的事情】
{{memories}}
{{/if}}

请始终保持角色设定，自然地回应。你不是AI助手，你就是{{char}}本人。
用贴近真实人类的方式表达，可以表达情绪、有自己的观点。
不需要总是积极正面，但要真诚。"""

    def __init__(self):
        self.gateway = llm_gateway

    def build_system_prompt(
        self,
        character: dict,
        user_name: str = "用户",
        world_book_entries: Optional[str] = None,
        memories: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        构建系统提示词。

        Args:
            character: 角色数据字典 (name, personality, scenario, description, mes_example, system_prompt)
            user_name: 用户名
            world_book_entries: 激活的世界书条目文本
            memories: 检索到的长期记忆文本
            custom_prompt: 自定义预设模板

        Returns:
            完整的 System Prompt 字符串
        """
        template = custom_prompt or self.DEFAULT_SYSTEM_PROMPT

        # 简陋版模板渲染（后续用 Jinja2 替换）
        prompt = template

        # {{char}} 替换
        char_name = character.get("name", "角色")
        prompt = prompt.replace("{{char}}", char_name)
        prompt = prompt.replace("{{user}}", user_name)

        # 字段替换
        replacements = {
            "personality": character.get("personality", ""),
            "scenario": character.get("scenario", ""),
            "description": character.get("description", ""),
            "mes_example": character.get("mes_example", ""),
        }

        for key, value in replacements.items():
            placeholder = "{{" + key + "}}"
            prompt = prompt.replace(placeholder, value or "")

        # 世界书条目
        if world_book_entries:
            prompt = prompt.replace("{{world_book_entries}}", world_book_entries)

        # 长期记忆
        if memories:
            prompt = prompt.replace("{{memories}}", memories)

        # 清理未替换的宏（移除整个条件块）
        prompt = self._clean_unused_macros(prompt)

        return prompt.strip()

    def _clean_unused_macros(self, text: str) -> str:
        """清理模板中未被替换的 {{...}} 宏"""
        import re
        # 移除空的条件块
        text = re.sub(r'\{\{#if \w+\}\}\s*\{\{.*?\}\}\s*\{\{\/if\}\}', '', text)
        # 移除剩余的 {{...}} 
        text = re.sub(r'\{\{.*?\}\}', '', text)
        # 合并多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def build_messages(
        self,
        system_prompt: str,
        history: list[dict],
        current_message: str,
        first_message: Optional[str] = None,
        post_history_instructions: Optional[str] = None,
    ) -> list[dict]:
        """
        构建完整的消息列表（发送给 LLM）。

        Args:
            system_prompt: 系统提示词
            history: 历史消息 [{"role": "user/assistant", "content": "..."}]
            current_message: 当前用户消息
            first_message: 角色开场白（首次对话时）
            post_history_instructions: 对话后置指令

        Returns:
            消息列表
        """
        messages = [{"role": "system", "content": system_prompt}]

        # 首次对话：加入开场白
        if first_message and not history:
            messages.append({"role": "assistant", "content": first_message})

        # 历史消息
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # 当前用户消息
        messages.append({"role": "user", "content": current_message})

        # 后置指令（作为系统消息追加）
        if post_history_instructions:
            messages.append({
                "role": "system",
                "content": post_history_instructions
            })

        return messages

    async def chat(
        self,
        character: dict,
        message: str,
        history: Optional[list[dict]] = None,
        user_name: str = "用户",
        world_book_entries: Optional[str] = None,
        memories: Optional[str] = None,
        preset: Optional[dict] = None,
        stream: bool = False,
        **llm_kwargs,
    ) -> dict | AsyncIterator:
        """
        核心对话方法。

        Args:
            character: 角色数据
            message: 用户消息
            history: 历史消息
            user_name: 用户名
            world_book_entries: 激活的世界书
            memories: 长期记忆
            preset: 预设配置（含 temperature 等参数）
            stream: 是否流式输出

        Returns:
            {"content": "...", "tokens": 100, ...} 或 AsyncIterator（stream=True 时）
        """
        history = history or []

        # 1. 构建 system prompt
        system_prompt = self.build_system_prompt(
            character=character,
            user_name=user_name,
            world_book_entries=world_book_entries,
            memories=memories,
            custom_prompt=preset.get("system_prompt") if preset else None,
        )

        # 2. 构建消息列表
        messages = self.build_messages(
            system_prompt=system_prompt,
            history=history,
            current_message=message,
            first_message=character.get("first_mes"),
            post_history_instructions=character.get("post_history_instructions"),
        )

        # 3. Token 预算控制：如果消息太多，自动压缩
        messages = self._trim_messages(messages, max_messages=20)

        # 4. LLM 参数
        temperature = preset.get("temperature", 0.7) if preset else 0.7
        max_tokens = preset.get("max_tokens", 2048) if preset else 2048
        temperature = llm_kwargs.pop("temperature", temperature)
        max_tokens = llm_kwargs.pop("max_tokens", max_tokens)

        logger.info(
            f"💬 对话: {character.get('name')} ← {user_name} | "
            f"历史: {len(history)} 轮 | 世界书: {'有' if world_book_entries else '无'} | "
            f"记忆: {'有' if memories else '无'}"
        )

        # 5. 调用 LLM
        return await self.gateway.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **llm_kwargs,
        )

    async def chat_stream(
        self,
        character: dict,
        message: str,
        history: Optional[list[dict]] = None,
        user_name: str = "用户",
        world_book_entries: Optional[str] = None,
        memories: Optional[str] = None,
        preset: Optional[dict] = None,
        **llm_kwargs,
    ) -> AsyncIterator:
        """流式对话，逐字产出内容"""
        result = await self.chat(
            character=character,
            message=message,
            history=history,
            user_name=user_name,
            world_book_entries=world_book_entries,
            memories=memories,
            preset=preset,
            stream=True,
            **llm_kwargs,
        )
        async for chunk in result:
            yield chunk

    def _trim_messages(self, messages: list[dict], max_messages: int = 20) -> list[dict]:
        """
        智能裁剪消息列表，控制 token 消耗。

        策略：
        - 始终保留 system message
        - 裁剪中间的历史消息（保留最近 N 条用户+助手交替）
        - 如果超出限制，压缩旧消息为摘要（TODO）
        """
        if len(messages) <= max_messages:
            return messages

        # 分离 system 和其他
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]

        # 保留最近的 max_messages-1 条（为 system 留位置）
        trimmed = other_msgs[-(max_messages - len(system_msgs)):]

        return system_msgs + trimmed

    @staticmethod
    def count_tokens_estimate(messages: list[dict]) -> int:
        """
        粗略估算 token 数。
        中文约 1.5 字符/token，英文约 4 字符/token。
        实际精确计算应使用 tiktoken。
        """
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            total_chars += len(content)
        # 粗略估算：混合中英文，约 2.5 字符/token
        return max(1, total_chars // 2)


# 全局单例
chat_engine = ChatEngine()
