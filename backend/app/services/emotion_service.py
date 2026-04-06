"""
表情分析服务 - 基于DeepFace
用于分析面试者的面部表情，判断紧张程度
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmotionService:
    """表情分析服务类"""

    def __init__(self):
        self.model_loaded = False
        self._model = None

    def _ensure_model(self):
        """延迟加载模型"""
        if not self.model_loaded:
            try:
                from deepface import DeepFace
                self._model = DeepFace
                self.model_loaded = True
                logger.info("DeepFace模型加载完成")
            except Exception as e:
                logger.error(f"DeepFace模型加载失败: {e}")
                self._model = None

    @staticmethod
    def calculate_nervousness(emotions: Dict[str, float]) -> float:
        """
        基于情绪计算紧张度 (0-100)

        权重设计:
        - fear: 高度紧张信号 (权重1.5)
        - sad: 中度紧张信号 (权重1.2)
        - angry: 中度紧张信号 (权重1.0)
        - disgust: 低度紧张信号 (权重0.8)
        - happy: 从容信号 (权重-1.0)
        - neutral: 从容信号 (权重-0.5)

        Args:
            emotions: 情绪置信度字典

        Returns:
            紧张度 0-100
        """
        fear = emotions.get("fear", 0)
        sad = emotions.get("sad", 0)
        angry = emotions.get("angry", 0)
        disgust = emotions.get("disgust", 0)
        happy = emotions.get("happy", 0)
        neutral = emotions.get("neutral", 0)

        # 计算原始紧张度分数
        raw_score = (
            fear * 1.5 + sad * 1.2 + angry * 1.0 + disgust * 0.8
            - happy * 1.0 - neutral * 0.5
        )

        # 归一化到 0-100
        # 假设 raw_score 范围大约是 -20 到 100
        nervousness = (raw_score + 20) / 120 * 100
        nervousness = max(0, min(100, nervousness))

        return round(nervousness, 1)

    def get_emotion_emoji(self, emotion: str) -> str:
        """
        获取情绪对应的表情图标

        Args:
            emotion: 情绪名称

        Returns:
            表情图标
        """
        emoji_map = {
            "happy": "😊",
            "sad": "😢",
            "angry": "😠",
            "fear": "😨",
            "surprise": "😲",
            "disgust": "🤢",
            "neutral": "🙂",
            "unknown": "❓"
        }
        return emoji_map.get(emotion.lower(), "🙂")

    def get_nervousness_level(self, nervousness: float) -> tuple:
        """
        根据紧张度获取等级和图标

        Args:
            nervousness: 紧张度 0-100

        Returns:
            (等级描述, 图标)
        """
        if nervousness >= 70:
            return "紧张", "😰"
        elif nervousness >= 40:
            return "一般", "😐"
        else:
            return "从容", "😊"

    def analyze_frame(self, image_path: str) -> Dict[str, Any]:
        """
        分析单帧图像的情绪

        Args:
            image_path: 图像文件路径

        Returns:
            {
                "emotion": str,           # 主要情绪
                "nervousness": float,     # 紧张度 0-100
                "all_emotions": dict,    # 所有情绪的置信度
                "emoji": str,            # 表情图标
                "level": str,            # 紧张等级
            }
        """
        self._ensure_model()

        if self._model is None:
            return {
                "emotion": "unknown",
                "nervousness": 0.0,
                "all_emotions": {},
                "emoji": "❓",
                "level": "分析失败"
            }

        try:
            from deepface import DeepFace

            # 分析情绪
            result = DeepFace.analyze(
                img_path=image_path,
                actions=["emotion"],
                detector_backend="retinaface",
                enforce_detection=False,  # 如果没检测到人脸也返回结果
            )

            if not result or len(result) == 0:
                return {
                    "emotion": "neutral",
                    "nervousness": 0.0,
                    "all_emotions": {},
                    "emoji": "🙂",
                    "level": "未检测到人脸"
                }

            emotions = result[0]["emotion"]
            dominant_emotion = max(emotions, key=emotions.get)
            nervousness = self.calculate_nervousness(emotions)
            level, emoji = self.get_nervousness_level(nervousness)

            return {
                "emotion": dominant_emotion,
                "nervousness": nervousness,
                "all_emotions": {k: round(v, 2) for k, v in emotions.items()},
                "emoji": emoji,
                "level": level
            }

        except Exception as e:
            logger.error(f"表情分析失败: {e}")
            return {
                "emotion": "unknown",
                "nervousness": 0.0,
                "all_emotions": {},
                "emoji": "❓",
                "level": "分析失败"
            }


# 单例
emotion_service = EmotionService()
