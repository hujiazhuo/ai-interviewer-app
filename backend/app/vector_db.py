"""
ChromaDB向量数据库连接
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional, List, Dict, Any

from app.config import settings


class VectorDB:
    client: Optional[chromadb.PersistentClient] = None

    @classmethod
    def connect(cls):
        """连接ChromaDB"""
        cls.client = chromadb.PersistentClient(
            path=settings.CHROMADB_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        print(f"Connected to ChromaDB: {settings.CHROMADB_PERSIST_DIR}")

    @classmethod
    def disconnect(cls):
        """断开ChromaDB连接"""
        cls.client = None
        print("Disconnected from ChromaDB")

    @classmethod
    def get_collection(cls, name: str):
        """获取collection"""
        if cls.client is None:
            cls.connect()
        return cls.client.get_collection(name=name)

    @classmethod
    def get_or_create_collection(cls, name: str, metadata: Optional[Dict] = None):
        """获取或创建collection"""
        if cls.client is None:
            cls.connect()
        return cls.client.get_or_create_collection(
            name=name,
            metadata=metadata or {"description": "Interview questions knowledge base"}
        )

    @classmethod
    def reset(cls):
        """重置数据库（谨慎使用）"""
        if cls.client:
            cls.client.reset()


# 快捷函数
def get_vector_collection(name: str = "interview_questions"):
    """获取面试题向量collection"""
    return VectorDB.get_or_create_collection(
        name=name,
        metadata={"description": "Interview questions for different positions"}
    )
