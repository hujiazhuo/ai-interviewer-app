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

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
