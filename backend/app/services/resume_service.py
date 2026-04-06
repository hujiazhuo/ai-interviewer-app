"""
简历服务
"""
import logging
import os
import uuid
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import fitz  # PyMuPDF
from docx import Document

from app.config import settings
from app.database import get_collection
from app.models.resume import ResumeModel, ResumeResponse

logger = logging.getLogger(__name__)


class ResumeParser:
    """简历解析器 - 提取结构化信息"""

    @staticmethod
    def parse_resume(content: str, file_type: str) -> Dict[str, Any]:
        """
        解析简历内容，提取结构化信息

        Returns:
            {
                "summary": str,  # 简历摘要
                "projects": List[Dict],  # 项目经验
                "skills": List[str],  # 技能列表
                "experience": List[Dict],  # 工作经历
            }
        """
        # 简单关键词匹配提取（后续可升级为 LLM 解析）
        content_lower = content.lower()

        # 提取技能关键词
        skill_keywords = [
            "python", "java", "go", "golang", "javascript", "typescript", "c++", "c#",
            "spring", "django", "flask", "fastapi", "react", "vue", "angular",
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "k8s", "jenkins", "git",
            "aws", "azure", "gcp", "阿里云", "腾讯云",
            "tensorflow", "pytorch", "sklearn", "langchain", "llm", "rag",
            "tcp", "udp", "http", "https", "websocket",
            "微服务", "分布式", "缓存", "消息队列", "架构设计",
        ]

        found_skills = []
        for skill in skill_keywords:
            if skill in content_lower:
                found_skills.append(skill)

        # 提取项目描述（简化：找包含项目关键字的段落）
        project_keywords = ["项目", "project", "系统", "平台", "开发", "实现"]
        project_sections = []
        lines = content.split("\n")
        current_project = []

        for line in lines:
            line_stripped = line.strip()
            # 如果行包含项目关键词，开始新项目
            if any(kw in line_stripped.lower() for kw in project_keywords):
                if current_project:
                    project_sections.append("\n".join(current_project))
                current_project = [line_stripped]
            elif current_project:
                current_project.append(line_stripped)

        if current_project:
            project_sections.append("\n".join(current_project))

        # 合并为摘要
        summary = content[:2000] if len(content) > 2000 else content

        return {
            "summary": summary,
            "projects": project_sections[:5],  # 最多5个项目
            "skills": list(set(found_skills))[:15],  # 最多15个技能
            "experience": [],  # 工作经历暂不提取
        }

    @staticmethod
    def format_for_prompt(parsed: Dict[str, Any]) -> str:
        """格式化简历为 LLM prompt"""
        parts = []

        if parsed.get("skills"):
            skills_str = ", ".join(parsed["skills"])
            parts.append(f"【技能】{skills_str}")

        if parsed.get("projects"):
            parts.append("【项目经历】")
            for i, proj in enumerate(parsed["projects"], 1):
                # 截取每个项目的前200字符
                proj_text = proj[:200] + "..." if len(proj) > 200 else proj
                parts.append(f"{i}. {proj_text}")

        return "\n\n".join(parts) if parts else ""


class ResumeService:
    @staticmethod
    def _ensure_upload_dir():
        """确保上传目录存在"""
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """解析PDF文件"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            logger.error(f"PDF解析错误: {e}")
        return text

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """解析DOCX文件"""
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            logger.error(f"DOCX解析错误: {e}")
        return text

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """解析TXT文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"TXT解析错误: {e}")
        return ""

    @staticmethod
    def _parse_file(file_path: str, file_type: str) -> str:
        """根据文件类型解析"""
        parsers = {
            "pdf": ResumeService._parse_pdf,
            "docx": ResumeService._parse_docx,
            "txt": ResumeService._parse_txt,
        }

        parser = parsers.get(file_type.lower())
        if parser:
            return parser(file_path)
        return ""

    @staticmethod
    def upload_resume(
        user_id: str,
        file_name: str,
        file_content: bytes,
    ) -> ResumeResponse:
        """
        上传简历

        Args:
            user_id: 用户ID
            file_name: 文件名
            file_content: 文件内容

        Returns:
            ResumeResponse
        """
        ResumeService._ensure_upload_dir()

        # 生成唯一文件名
        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt"
        unique_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 解析内容
        parsed_content = ResumeService._parse_file(file_path, file_ext)

        # 解析结构化信息
        parsed_data = ResumeParser.parse_resume(parsed_content, file_ext)

        # 保存到数据库
        resumes = get_collection("resumes")
        resume_doc = {
            "user_id": user_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_type": file_ext,
            "uploaded_at": datetime.utcnow(),
            "parsed_content": parsed_content,
            "parsed_skills": parsed_data.get("skills", []),
            "parsed_projects": parsed_data.get("projects", []),
            "parsed_summary": parsed_data.get("summary", ""),
        }

        result = resumes.insert_one(resume_doc)
        resume_doc["_id"] = result.inserted_id

        return ResumeResponse(
            id=str(resume_doc["_id"]),
            user_id=user_id,
            file_name=file_name,
            file_type=file_ext,
            uploaded_at=resume_doc["uploaded_at"],
            parsed_content=parsed_content,
        )

    @staticmethod
    def get_user_resumes(user_id: str) -> List[ResumeResponse]:
        """获取用户的所有简历"""
        resumes = get_collection("resumes")
        cursor = resumes.find({"user_id": user_id}).sort("uploaded_at", -1)

        result = []
        for doc in cursor:
            result.append(ResumeResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                file_name=doc["file_name"],
                file_type=doc["file_type"],
                uploaded_at=doc["uploaded_at"],
                parsed_content=doc.get("parsed_content"),
                parsed_skills=doc.get("parsed_skills", []),
                parsed_projects=doc.get("parsed_projects", []),
            ))

        return result

    @staticmethod
    def get_resume(resume_id: str, user_id: str) -> Optional[ResumeResponse]:
        """获取单个简历"""
        resumes = get_collection("resumes")

        try:
            doc = resumes.find_one({"_id": ObjectId(resume_id), "user_id": user_id})
            if doc:
                return ResumeResponse(
                    id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    file_name=doc["file_name"],
                    file_type=doc["file_type"],
                    uploaded_at=doc["uploaded_at"],
                    parsed_content=doc.get("parsed_content"),
                )
        except Exception:
            pass

        return None

    @staticmethod
    def delete_resume(resume_id: str, user_id: str) -> bool:
        """删除简历"""
        resumes = get_collection("resumes")

        try:
            # 获取简历信息以删除文件
            doc = resumes.find_one({"_id": ObjectId(resume_id), "user_id": user_id})
            if doc and doc.get("file_path"):
                try:
                    os.remove(doc["file_path"])
                except Exception:
                    pass

            # 删除数据库记录
            result = resumes.delete_one({"_id": ObjectId(resume_id), "user_id": user_id})
            return result.deleted_count > 0
        except Exception:
            return False
