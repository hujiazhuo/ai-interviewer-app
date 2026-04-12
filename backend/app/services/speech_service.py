"""
语音服务 - STT/TTS处理
- STT: faster-whisper (本地运行，支持中文)
- TTS: edge-tts (微软Neural声音，完全免费)
"""
import asyncio
import logging
import os
import uuid
from typing import Optional, AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)

# 持久化音频存储目录（Sealos DevBox 容器重启后不会丢失）
PERSISTENT_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "audio_files")
os.makedirs(PERSISTENT_AUDIO_DIR, exist_ok=True)
logger.info(f"音频存储目录: {PERSISTENT_AUDIO_DIR}")


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

                # 优先加载本地缓存快照，离线环境避免联网拉取模型失败
                model_source = self._resolve_stt_model_source()
                self.stt_model = WhisperModel(
                    model_source,
                    device=settings.STT_DEVICE,
                    compute_type="int8"
                )
                self._stt_initialized = True
                logger.info(f"STT模型加载完成: source={model_source}, device={settings.STT_DEVICE}")
            except Exception as e:
                logger.error(f"STT模型加载失败: {e}")
                self.stt_model = None

    def _resolve_stt_model_source(self) -> str:
        """解析STT模型来源：优先本地快照，其次模型名"""
        cache_root = settings.HUGGINGFACE_HUB_CACHE_DIR
        repo_id = f"Systran/faster-whisper-{settings.STT_MODEL_SIZE}"
        repo_dir = os.path.join(cache_root, f"models--{repo_id.replace('/', '--')}")

        refs_main = os.path.join(repo_dir, "refs", "main")
        if os.path.isfile(refs_main):
            with open(refs_main, "r", encoding="utf-8") as f:
                snapshot_id = f.read().strip()
            snapshot_dir = os.path.join(repo_dir, "snapshots", snapshot_id)
            if os.path.isdir(snapshot_dir):
                return snapshot_dir

        snapshots_dir = os.path.join(repo_dir, "snapshots")
        if os.path.isdir(snapshots_dir):
            candidates = [
                os.path.join(snapshots_dir, d)
                for d in os.listdir(snapshots_dir)
                if os.path.isdir(os.path.join(snapshots_dir, d))
            ]
            if candidates:
                candidates.sort(key=os.path.getmtime, reverse=True)
                return candidates[0]

        # 找不到本地缓存时回退到模型名（可能触发下载）
        return settings.STT_MODEL_SIZE

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
            logger.error("STT模型未加载")
            return ""

        if not os.path.exists(audio_path):
            logger.error(f"音频文件不存在: {audio_path}")
            return ""

        file_size = os.path.getsize(audio_path)
        if file_size <= 0:
            logger.error(f"音频文件为空: {audio_path}")
            return ""

        logger.info(f"开始STT转写，文件: {audio_path}, 大小: {file_size} bytes")

        # faster-whisper 是同步的，在线程池中运行
        loop = asyncio.get_running_loop()

        def _transcribe(vad_filter: bool, beam_size: int) -> str:
            segments, _ = self.stt_model.transcribe(
                audio_path,
                language="zh",
                vad_filter=vad_filter,
                beam_size=beam_size,
            )
            return "".join(seg.text for seg in segments).strip()

        try:
            # 首次尝试：开启VAD，适合常规语音
            text = await loop.run_in_executor(None, lambda: _transcribe(True, 5))
            if text:
                logger.info(f"STT转写结果: '{text}'")
                return text

            # 降级重试：关闭VAD，避免短音频或低音量被过滤
            logger.warning("STT首次结果为空，使用无VAD模式重试")
            text = await loop.run_in_executor(None, lambda: _transcribe(False, 1))
            if text:
                logger.info(f"STT降级重试成功: '{text}'")
                return text

            logger.warning("STT转写结果为空")
            return ""
        except Exception as e:
            logger.error(f"STT转写异常: {e}")
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
            # 使用持久化存储目录，替代 /tmp（容器重启后会丢失）
            output_path = os.path.join(PERSISTENT_AUDIO_DIR, f"tts_{uuid.uuid4()}{suffix}")

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
