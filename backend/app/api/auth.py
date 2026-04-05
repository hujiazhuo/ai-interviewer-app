"""
认证API
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.models import UserCreate, UserLogin, UserResponse
from app.services import AuthService
from app.utils.security import decode_access_token


router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    return payload


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """用户注册"""
    result = AuthService.register(user_data)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "success": True,
        "user": {
            "id": result["user"].id,
            "username": result["user"].username,
            "created_at": result["user"].created_at.isoformat(),
        }
    }


@router.post("/login", response_model=dict)
async def login(login_data: UserLogin):
    """用户登录"""
    result = AuthService.login(login_data.username, login_data.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])

    return {
        "success": True,
        "token": result["token"],
        "user": {
            "id": result["user"].id,
            "username": result["user"].username,
            "created_at": result["user"].created_at.isoformat(),
        }
    }


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user = AuthService.get_user_by_id(current_user["sub"])

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
    }
