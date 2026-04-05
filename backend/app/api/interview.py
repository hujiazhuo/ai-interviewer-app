"""
面试API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models import InterviewCreate, AnswerSubmit
from app.services import InterviewService, ResumeService
from app.utils.security import decode_access_token
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/interview", tags=["面试"])


@router.post("/start", response_model=dict)
async def start_interview(
    interview_data: InterviewCreate,
    current_user: dict = Depends(get_current_user),
):
    """开始面试"""
    user_id = current_user["sub"]
    position = interview_data.position

    # 验证岗位
    valid_positions = ["backend", "algorithm", "network"]
    if position not in valid_positions:
        raise HTTPException(
            status_code=400,
            detail=f"无效的岗位类型，仅支持: {', '.join(valid_positions)}"
        )

    # 创建面试
    interview = InterviewService.start_interview(user_id, position)

    # 获取第一个问题
    first_question = InterviewService.get_next_question(
        interview_id=interview.id,
        user_id=user_id,
    )

    return {
        "success": True,
        "interview_id": interview.id,
        "position": position,
        "opening": first_question.get("opening", ""),
        "question": first_question.get("question", ""),
        "question_id": first_question.get("question_id", ""),
        "question_count": 1,
        "is_personalized": first_question.get("is_personalized", False),
    }


@router.post("/{interview_id}/question", response_model=dict)
async def get_next_question(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取下一个问题"""
    user_id = current_user["sub"]

    # 获取用户项目经历
    resume_content = InterviewService._get_user_resume_content(user_id)

    result = InterviewService.get_next_question(
        interview_id=interview_id,
        user_id=user_id,
        resume_content=resume_content,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "success": True,
        "question": result.get("question"),
        "question_id": result.get("question_id"),
        "opening": result.get("opening", ""),
        "is_first": result.get("is_first", False),
        "is_finished": result.get("is_finished", False),
        "question_count": result.get("question_count", 0),
        "is_personalized": result.get("is_personalized", False),
    }


@router.post("/{interview_id}/answer", response_model=dict)
async def submit_answer(
    interview_id: str,
    answer_data: AnswerSubmit,
    current_user: dict = Depends(get_current_user),
):
    """提交回答"""
    user_id = current_user["sub"]

    # 获取面试信息
    interview = InterviewService.get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    if interview.status.value == "completed":
        raise HTTPException(status_code=400, detail="面试已结束")

    # 获取当前问题ID（最后一个问题）
    current_question = interview.questions[-1] if interview.questions else None
    if not current_question:
        raise HTTPException(status_code=400, detail="当前没有问题")

    # 提交回答
    result = InterviewService.submit_answer(
        interview_id=interview_id,
        user_id=user_id,
        question_id=current_question.question_id,
        answer=answer_data.answer,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "success": True,
        "comment": result.get("comment"),
        "score": result.get("score"),
        "technical": result.get("technical", 5.0),
        "communication": result.get("communication", 5.0),
        "problem_solving": result.get("problem_solving", 5.0),
        "experience": result.get("experience", 5.0),
        "logical_thinking": result.get("logical_thinking", 5.0),
        "correct_answer": result.get("correct_answer", ""),
        "is_finished": result.get("is_finished", False),
        "question_count": result.get("question_count", 0),
    }


@router.get("/{interview_id}", response_model=dict)
async def get_interview_status(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取面试状态"""
    user_id = current_user["sub"]

    interview = InterviewService.get_interview(interview_id)

    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    if interview.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权限")

    return {
        "success": True,
        "interview": {
            "id": interview.id,
            "position": interview.position,
            "status": interview.status.value,
            "question_count": len(interview.questions),
            "total_score": interview.total_score,
            "started_at": interview.started_at.isoformat(),
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "questions": [
                {
                    "question": q.question,
                    "answer": q.answer,
                    "comment": q.comment,
                    "score": q.score,
                }
                for q in interview.questions
            ],
        }
    }


@router.post("/{interview_id}/end", response_model=dict)
async def end_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """结束面试"""
    user_id = current_user["sub"]

    result = InterviewService.end_interview(interview_id, user_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "success": True,
        "total_score": result.get("total_score"),
        "dimension_scores": result.get("dimension_scores"),
        "question_count": result.get("question_count"),
    }


@router.delete("/{interview_id}", response_model=dict)
async def delete_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除面试记录"""
    user_id = current_user["sub"]

    success = InterviewService.delete_interview(interview_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="面试记录不存在或无权限删除")

    return {"success": True}
