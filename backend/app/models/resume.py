"""
简历模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResumeModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    file_name: str
    file_path: str
    file_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    parsed_content: Optional[str] = None  # 解析后的简历文本

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: str
    uploaded_at: datetime
    parsed_content: Optional[str] = None
    parsed_skills: Optional[list] = Field(default_factory=list)
    parsed_projects: Optional[list] = Field(default_factory=list)

    class Config:
        from_attributes = True
