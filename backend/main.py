"""
AI Interviewer - FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import MongoDB
from app.vector_db import VectorDB
from app.api import (
    auth_router,
    resume_router,
    interview_router,
    interview_voice_router,
    score_router,
    knowledge_router,
    project_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("=" * 50)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 50)

    # 连接数据库
    MongoDB.connect()
    MongoDB.create_indexes()

    # 连接向量数据库
    VectorDB.connect()

    print("All connections established!")
    print("=" * 50)

    yield

    # 关闭时
    print("Shutting down...")
    MongoDB.disconnect()
    VectorDB.disconnect()
    print("Goodbye!")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI面试官平台 - 后端API",
    lifespan=lifespan,
)

# 配置CORS - 生产环境应限制来源
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # 开发环境
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # 小程序环境
    "http://servicewechat.com",
    "wx://servicewechat.com",
]
if settings.DEBUG:
    # 开发环境允许所有来源
    ALLOWED_ORIGINS.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(interview_voice_router)
app.include_router(score_router)
app.include_router(knowledge_router)
app.include_router(project_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mongodb": MongoDB.client is not None,
        "chromadb": VectorDB.client is not None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=settings.DEBUG,
    )
