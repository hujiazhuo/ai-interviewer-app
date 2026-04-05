"""
评分模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class DimensionScores(BaseModel):
    technical: float = 0.0
    communication: float = 0.0
    problem_solving: float = 0.0
    experience: float = 0.0
    logical_thinking: float = 0.0


class ScoreModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    interview_id: str
    position: str
    total_score: float
    dimension_scores: DimensionScores
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ScoreResponse(BaseModel):
    id: str
    user_id: str
    interview_id: str
    position: str
    total_score: float
    dimension_scores: DimensionScores
    created_at: datetime

    class Config:
        from_attributes = True


class RadarChartData(BaseModel):
    labels: List[str] = [
        "技术能力",
        "沟通表达",
        "问题解决",
        "项目经验",
        "逻辑思维"
    ]
    technical: float
    communication: float
    problem_solving: float
    experience: float
    logical_thinking: float
