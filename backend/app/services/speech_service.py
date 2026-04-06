"""
语音服务 - STT/TTS处理
- STT: faster-whisper (本地运行，支持中文)
- TTS: edge-tts (微软Neural声音，完全免费)
"""
import asyncio
import logging
import tempfile
import os
import uuid
from typing import Optional, AsyncGenerator
from functools import lru_cache

logger = logging.getLogger(__name__)


class SpeechService:
    """语音服务类"""

    def __init__(self):
        self.stt_model = None
        self._stt_initialized = False
        # TTS默认语音 - 女声(晓晓)
        self.default_voice = "zh-CN-XiaoxiaoNeural"

    def _init_stt(self):
        """延迟初始化STT模型（节省启动时间）"""
        if not self._stt_initialized:
            try:
                from faster_whisper import WhisperModel
                # 使用base模型平衡速度和准确率
                # 可选: tiny, base, small, medium, large
                self.stt_model = WhisperModel(
                    "base",
                    device="cpu",
                    compute_type="int8"
                )
                self._stt_initialized = True
                logger.info("STT模型加载完成 (base, CPU)")
            except Exception as e:
                logger.error(f"STT模型加载失败: {e}")
                self.stt_model = None

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        语音转文字 (STT)

        Args:
            audio_path: 音频文件路径

        Returns:
            识别的文本
        """
        self._init_stt()

        if self.stt_model is None:
            return ""

        # faster-whisper 是同步的，在线程池中运行
        loop = asyncio.get_event_loop()

        def _transcribe():
            segments, _ = self.stt_model.transcribe(
                audio_path,
                language="zh",
                vad_filter=True,  # 语音活动检测，过滤静音
                beam_size=5,
            )
            return "".join([seg.text for seg in segments])

        try:
            text = await loop.run_in_executor(None, _transcribe)
            return text.strip()
        except Exception as e:
            logger.error(f"STT转写失败: {e}")
            return ""

    async def text_to_speech(self, text: str, output_path: Optional[str] = None, voice: Optional[str] = None) -> str:
        """
        文字转语音 (TTS)

        Args:
            text: 要转换的文本
            output_path: 输出文件路径，不传则自动生成
            voice: 语音名称，默认晓晓(女声)

        Returns:
            生成的音频文件路径
        """
        if output_path is None:
            suffix = ".mp3"
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_{uuid.uuid4()}{suffix}")

        voice = voice or self.default_voice

        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"TTS合成失败: {e}")
            return ""

    async def text_to_speech_stream(self, text: str, voice: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """
        流式TTS (用于WebSocket实时传输)

        Args:
            text: 要转换的文本
            voice: 语音名称

        Yields:
            音频数据块
        """
        voice = voice or self.default_voice

        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"TTS流式合成失败: {e}")

    def get_available_voices(self) -> dict:
        """
        获取可用的中文语音列表

        Returns:
            语音字典 {voice_name: description}
        """
        return {
            "zh-CN-XiaoxiaoNeural": "晓晓（女声，推荐）",
            "zh-CN-YunxiNeural": "云希（男声）",
            "zh-CN-YunyangNeural": "云扬（男声，新闻）",
            "zh-CN-XiaoyiNeural": "小艺（女声）",
        }


# 单例
speech_service = SpeechService()
