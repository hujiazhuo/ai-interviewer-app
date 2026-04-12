"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI Interviewer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # MongoDB配置 (Sealos)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_interviewer"

    # ChromaDB配置 (本地向量数据库)
    CHROMADB_PERSIST_DIR: str = "./chroma_db"

    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Hugging Face配置
    HUGGINGFACE_ENDPOINT: str = "https://hf-mirror.com"
    HUGGINGFACE_EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    HUGGINGFACE_MODEL_LOCAL_DIR: str = "./models/paraphrase-multilingual-MiniLM-L12-v2"
    HUGGINGFACE_HUB_CACHE_DIR: str = "./models/hub"
    HUGGINGFACE_LOCAL_ONLY: bool = False

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 面试配置
    MAX_QUESTIONS_PER_INTERVIEW: int = 10

    # 评分权重
    SCORE_WEIGHTS: dict = {
        "technical": 0.4,
        "communication": 0.2,
        "problem_solving": 0.2,
        "experience": 0.1,
        "logical_thinking": 0.1,
    }

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # STT配置 (语音转文字)
    STT_MODEL_SIZE: str = "base"  # tiny/base/small/medium/large
    STT_DEVICE: str = "cpu"  # cpu/cuda

    # TTS配置 (文字转语音)
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"  # 默认女声(晓晓)

    # 表情分析配置
    EMOTION_DETECTOR: str = "retinaface"  #  retinaface/ssd/mtcnn
    EMOTION_MODEL: str = "Facenet512"  # VGG-Face/Facenet/Facenet512/DeepFace

    # WebSocket配置
    VOICE_SESSION_TIMEOUT: int = 300  # 5分钟

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
