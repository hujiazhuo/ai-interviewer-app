"""
评分API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.services import ScoreService
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/score", tags=["评分"])


@router.get("/history", response_model=dict)
async def get_score_history(
    position: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """获取评分历史"""
    user_id = current_user["sub"]

    scores = ScoreService.get_user_scores(user_id, position, limit)

    return {
        "success": True,
        "scores": [
            {
                "id": s.id,
                "interview_id": s.interview_id,
                "position": s.position,
                "total_score": s.total_score,
                "dimension_scores": {
                    "technical": s.dimension_scores.technical,
                    "communication": s.dimension_scores.communication,
                    "problem_solving": s.dimension_scores.problem_solving,
                    "experience": s.dimension_scores.experience,
                    "logical_thinking": s.dimension_scores.logical_thinking,
                },
                "created_at": s.created_at.isoformat(),
            }
            for s in scores
        ]
    }


@router.get("/radar", response_model=dict)
async def get_radar_chart_data(
    current_user: dict = Depends(get_current_user),
):
    """获取雷达图数据"""
    user_id = current_user["sub"]

    radar_data = ScoreService.get_radar_chart_data(user_id)

    return {
        "success": True,
        "radar": {
            "labels": radar_data.labels,
            "data": [
                radar_data.technical,
                radar_data.communication,
                radar_data.problem_solving,
                radar_data.experience,
                radar_data.logical_thinking,
            ]
        }
    }


@router.get("/trend", response_model=dict)
async def get_score_trend(
    position: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """获取评分趋势"""
    user_id = current_user["sub"]

    trend = ScoreService.get_score_trend(user_id, position, limit)

    return {
        "success": True,
        "trend": trend,
    }


@router.get("/position-avg", response_model=dict)
async def get_average_by_position(
    current_user: dict = Depends(get_current_user),
):
    """获取各岗位平均分"""
    user_id = current_user["sub"]

    avg_scores = ScoreService.get_average_score_by_position(user_id)

    return {
        "success": True,
        "position_scores": avg_scores,
    }
