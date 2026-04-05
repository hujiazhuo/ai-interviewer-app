"""
认证服务
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId

from app.database import get_collection
from app.models import UserCreate, UserResponse, UserModel
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    def register(user_data: UserCreate) -> Dict[str, Any]:
        """用户注册"""
        users = get_collection("users")

        # 检查用户名是否已存在
        existing = users.find_one({"username": user_data.username})
        if existing:
            return {"success": False, "error": "用户名已存在"}

        # 创建用户
        user_doc = {
            "username": user_data.username,
            "password_hash": hash_password(user_data.password),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        return {
            "success": True,
            "user": UserResponse(
                id=str(user_doc["_id"]),
                username=user_doc["username"],
                created_at=user_doc["created_at"],
            )
        }

    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        users = get_collection("users")

        # 查找用户
        user = users.find_one({"username": username})
        if not user:
            return {"success": False, "error": "用户名或密码错误"}

        # 验证密码
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "error": "用户名或密码错误"}

        # 生成token
        token = create_access_token(
            data={
                "sub": str(user["_id"]),
                "username": user["username"],
            }
        )

        return {
            "success": True,
            "token": token,
            "user": UserResponse(
                id=str(user["_id"]),
                username=user["username"],
                created_at=user["created_at"],
            )
        }

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        users = get_collection("users")

        try:
            user = users.find_one({"_id": ObjectId(user_id)})
            if user:
                return UserResponse(
                    id=str(user["_id"]),
                    username=user["username"],
                    created_at=user["created_at"],
                )
        except Exception:
            pass

        return None
