"""
MongoDB数据库连接
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional

from app.config import settings


class MongoDB:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    @classmethod
    def connect(cls):
        """连接MongoDB"""
        cls.client = MongoClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.MONGODB_DB_NAME]
        print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

    @classmethod
    def disconnect(cls):
        """断开MongoDB连接"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("Disconnected from MongoDB")

    @classmethod
    def get_collection(cls, name: str) -> Collection:
        """获取collection"""
        if cls.db is None:
            cls.connect()
        return cls.db[name]

    @classmethod
    def create_indexes(cls):
        """创建必要的索引"""
        # users collection - username唯一索引
        users = cls.get_collection("users")
        users.create_index("username", unique=True)

        # resumes collection - user_id索引
        resumes = cls.get_collection("resumes")
        resumes.create_index("user_id")

        # interviews collection - user_id和position索引
        interviews = cls.get_collection("interviews")
        interviews.create_index("user_id")
        interviews.create_index("position")
        interviews.create_index([("user_id", 1), ("position", 1)])

        # scores collection - user_id和时间索引
        scores = cls.get_collection("scores")
        scores.create_index("user_id")
        scores.create_index("created_at")


# 快捷函数
def get_db() -> Database:
    return MongoDB.db


def get_collection(name: str) -> Collection:
    return MongoDB.get_collection(name)
