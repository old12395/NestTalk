"""多模态引擎 — 识图/生图/语音识别/语音合成"""

import os
import tempfile
from typing import Optional
from loguru import logger

from app.services.llm_gateway.gateway import llm_gateway
from app.core.config import settings


class MultimodalEngine:
    """多模态引擎，LLM 可通过 function calling 调用这些能力"""

    # ─── 图片识别 ─────────────────────────────

    async def vision(self, image_url: str, prompt: str = "请详细描述这张图片的内容") -> str:
        """识别图片内容"""
        model = settings.VISION_MODEL or settings.LLM_MODEL
        provider = settings.VISION_PROVIDER

        try:
            result = await llm_gateway.vision(
                prompt=prompt,
                image_url=image_url,
                model=model,
                provider=provider,
                api_key=settings.VISION_API_KEY or None,
                base_url=getattr(settings, 'VISION_BASE_URL', None),
            )
            logger.info(f"🖼️ 识图完成: {model}")
            return result
        except Exception as e:
            logger.error(f"识图失败: {e}")
            return ""

    # ─── 图片生成 ─────────────────────────────

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> Optional[str]:
        """
        生成图片。

        Returns:
            图片 URL，失败返回 None
        """
        provider = settings.IMAGE_PROVIDER
        model = settings.IMAGE_MODEL

        if not provider or provider == "openai":
            try:
                client = llm_gateway._get_client(
                    provider="openai",
                    api_key=settings.IMAGE_API_KEY or settings.LLM_API_KEY,
                    base_url=settings.LLM_BASE_URL,
                )
                response = await client.images.generate(
                    model=model or "dall-e-3",
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1,
                )
                url = response.data[0].url
                logger.info(f"🎨 生图完成: {prompt[:30]}...")
                return url
            except Exception as e:
                logger.error(f"生图失败: {e}")
                return None

        # Stable Diffusion
        if provider == "sd":
            # TODO: Stable Diffusion API
            logger.warning("Stable Diffusion 暂未实现")
            return None

        return None

    # ─── 语音识别 (STT) ──────────────────────

    async def speech_to_text(self, audio_data: bytes, language: str = "zh") -> str:
        """
        语音转文字。

        Args:
            audio_data: 音频文件字节
            language: 语言代码

        Returns:
            识别的文本
        """
        provider = settings.STT_PROVIDER

        if not provider or provider == "openai":
            try:
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                    f.write(audio_data)
                    tmp_path = f.name

                client = llm_gateway._get_client(
                    provider="openai",
                    api_key=settings.STT_API_KEY or settings.LLM_API_KEY,
                    base_url=settings.LLM_BASE_URL,
                )

                with open(tmp_path, "rb") as audio_file:
                    transcript = await client.audio.transcriptions.create(
                        model=settings.STT_MODEL or "whisper-1",
                        file=audio_file,
                        language=language,
                    )

                os.unlink(tmp_path)
                text = transcript.text
                logger.info(f"🎤 STT: {text[:50]}...")
                return text

            except Exception as e:
                logger.error(f"语音识别失败: {e}")
                return ""

        return ""

    # ─── 语音合成 (TTS) ──────────────────────

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        文字转语音。

        Args:
            text: 要合成的文字
            voice: 语音角色
            speed: 语速

        Returns:
            音频字节数据
        """
        provider = settings.TTS_PROVIDER or "edge_tts"
        voice = voice or settings.TTS_VOICE

        # Edge TTS (免费)
        if provider == "edge_tts":
            try:
                import edge_tts
                communicate = edge_tts.Communicate(text, voice, rate=f"+{int((speed-1)*100)}%" if speed != 1 else "+0%")
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                result = b"".join(audio_chunks)
                logger.info(f"🔊 TTS (Edge): {text[:30]}... ({len(result)} bytes)")
                return result
            except ImportError:
                logger.warning("edge-tts 未安装，TTS 不可用")
                return None
            except Exception as e:
                logger.error(f"TTS 失败: {e}")
                return None

        # OpenAI TTS
        if provider == "openai":
            try:
                client = llm_gateway._get_client(
                    provider="openai",
                    api_key=settings.TTS_API_KEY or settings.LLM_API_KEY,
                    base_url=settings.LLM_BASE_URL,
                )
                response = await client.audio.speech.create(
                    model=settings.TTS_MODEL or "tts-1",
                    voice=voice or "alloy",
                    input=text,
                    speed=speed,
                )
                result = response.content
                logger.info(f"🔊 TTS (OpenAI): {text[:30]}...")
                return result
            except Exception as e:
                logger.error(f"TTS 失败: {e}")
                return None

        return None


# 全局单例
multimodal_engine = MultimodalEngine()
