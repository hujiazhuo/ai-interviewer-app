"""
面试记录模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InterviewStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InterviewQuestion(BaseModel):
    question_id: str
    question: str
    answer: Optional[str] = None
    comment: Optional[str] = None  # 点评（含正确答案）
    score: Optional[float] = None  # 单题得分
    # 独立维度分数
    technical: Optional[float] = None
    communication: Optional[float] = None
    problem_solving: Optional[float] = None
    experience: Optional[float] = None
    logical_thinking: Optional[float] = None
    is_generated: bool = False  # 是否为大模型生成的题目
    is_personalized: bool = False  # 是否为个性化题目（基于简历）
    correct_answer: Optional[str] = None  # 标准答案（知识库题目才有）
    kb_id: Optional[str] = None  # 知识库题目ID（用于去重）


class InterviewModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    position: str  # frontend/backend/algorithm
    mode: str = "text"  # text | voice
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    questions: List[InterviewQuestion] = []
    total_score: Optional[float] = None
    nervousness_history: List[dict] = []  # 紧张度历史记录
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class InterviewCreate(BaseModel):
    position: str


class InterviewResponse(BaseModel):
    id: str
    user_id: str
    position: str
    status: str
    question_count: int
    total_score: Optional[float] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    answer: str


class AnswerResponse(BaseModel):
    question: str
    comment: str  # 点评
    next_question: Optional[str] = None
    is_finished: bool = False
    score: Optional[float] = None
