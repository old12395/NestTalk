"""LLM 网关 — 统一的多模型调用接口"""

from typing import AsyncIterator, Optional
from openai import AsyncOpenAI
from loguru import logger
from app.core.config import settings


class LLMGateway:
    """LLM 调用网关，支持多种模型，自动回退"""

    def __init__(self):
        self._clients: dict[str, AsyncOpenAI] = {}

    def _get_client(self, provider: str = None, api_key: str = None, base_url: str = None) -> AsyncOpenAI:
        """获取或创建客户端"""
        provider = provider or settings.LLM_PROVIDER
        api_key = api_key or settings.LLM_API_KEY
        base_url = base_url or settings.LLM_BASE_URL

        cache_key = f"{provider}:{api_key}:{base_url}"
        if cache_key not in self._clients:
            self._clients[cache_key] = AsyncOpenAI(api_key=api_key, base_url=base_url)
        return self._clients[cache_key]

    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        provider: str = None,
        api_key: str = None,
        base_url: str = None,
    ) -> dict | AsyncIterator:
        """
        发送对话请求。

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名，默认使用配置的主模型
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            provider: 模型提供方
            api_key: API Key
            base_url: API Base URL

        Returns:
            dict: {"content": "...", "tokens": 100, "model": "..."}
            或 AsyncIterator（流式输出时）
        """
        model = model or settings.LLM_MODEL
        client = self._get_client(provider, api_key, base_url)

        logger.info(f"🤖 LLM 请求 → {model} | messages: {len(messages)} | stream: {stream}")

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )

            if stream:
                return self._stream_response(response, model)
            else:
                choice = response.choices[0]
                return {
                    "content": choice.message.content,
                    "tokens": response.usage.total_tokens if response.usage else 0,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "model": model,
                    "finish_reason": choice.finish_reason,
                }

        except Exception as e:
            logger.error(f"🤖 LLM 调用失败 ({model}): {e}")

            # 自动回退到备用模型
            if settings.FALLBACK_MODEL and settings.FALLBACK_MODEL != model:
                logger.info(f"🔄 回退到备用模型: {settings.FALLBACK_MODEL}")
                return await self.chat(
                    messages=messages,
                    model=settings.FALLBACK_MODEL,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    provider=settings.FALLBACK_PROVIDER,
                    api_key=settings.FALLBACK_API_KEY,
                    base_url=settings.FALLBACK_BASE_URL,
                )

            raise

    async def _stream_response(self, response, model: str) -> AsyncIterator:
        """处理流式响应，逐个产出 content 片段"""
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def vision(
        self,
        prompt: str,
        image_url: str,
        model: str = None,
        provider: str = None,
        api_key: str = None,
        base_url: str = None,
    ) -> str:
        """识图能力"""
        model = model or settings.VISION_MODEL or settings.LLM_MODEL
        client = self._get_client(
            provider or settings.VISION_PROVIDER or settings.LLM_PROVIDER,
            api_key or settings.VISION_API_KEY or settings.LLM_API_KEY,
            base_url or getattr(settings, "VISION_BASE_URL", None) or settings.LLM_BASE_URL,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        response = await client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content or ""


# 全局单例
llm_gateway = LLMGateway()
