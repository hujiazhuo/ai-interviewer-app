"""
API package
"""
from app.api.auth import router as auth_router
from app.api.resume import router as resume_router
from app.api.interview import router as interview_router
from app.api.score import router as score_router
from app.api.knowledge import router as knowledge_router
from app.api.project import router as project_router

__all__ = [
    "auth_router",
    "resume_router",
    "interview_router",
    "score_router",
    "knowledge_router",
    "project_router",
]
