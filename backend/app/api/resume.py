"""
简历API
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List

from app.models import ResumeResponse
from app.services import ResumeService
from app.utils.security import decode_access_token
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/resume", tags=["简历"])


@router.post("/upload", response_model=dict)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传简历"""
    user_id = current_user["sub"]

    # 验证文件类型
    allowed_types = ["pdf", "docx", "txt"]
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(allowed_types)}"
        )

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    # 上传简历
    result = ResumeService.upload_resume(
        user_id=user_id,
        file_name=file.filename,
        file_content=content,
    )

    return {
        "success": True,
        "resume": {
            "id": result.id,
            "file_name": result.file_name,
            "file_type": result.file_type,
            "uploaded_at": result.uploaded_at.isoformat(),
        }
    }


@router.get("/list", response_model=dict)
async def get_resumes(current_user: dict = Depends(get_current_user)):
    """获取用户简历列表"""
    user_id = current_user["sub"]

    resumes = ResumeService.get_user_resumes(user_id)

    return {
        "success": True,
        "resumes": [
            {
                "id": r.id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "uploaded_at": r.uploaded_at.isoformat(),
                "parsed_content": r.parsed_content[:500] + "..." if r.parsed_content and len(r.parsed_content) > 500 else r.parsed_content,
            }
            for r in resumes
        ]
    }


@router.get("/{resume_id}", response_model=dict)
async def get_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取单个简历"""
    user_id = current_user["sub"]

    resume = ResumeService.get_resume(resume_id, user_id)

    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    return {
        "success": True,
        "resume": {
            "id": resume.id,
            "file_name": resume.file_name,
            "file_type": resume.file_type,
            "uploaded_at": resume.uploaded_at.isoformat(),
            "parsed_content": resume.parsed_content,
        }
    }


@router.delete("/{resume_id}", response_model=dict)
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除简历"""
    user_id = current_user["sub"]

    success = ResumeService.delete_resume(resume_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="简历不存在或删除失败")

    return {"success": True}
