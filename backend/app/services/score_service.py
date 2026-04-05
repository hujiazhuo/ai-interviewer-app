"""
评分服务 - 综合评分和雷达图数据
"""
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.config import settings
from app.database import get_collection
from app.models.score import ScoreModel, DimensionScores, RadarChartData, ScoreResponse


class ScoreService:
    # 时间衰减系数
    DECAY_LAMBDA = 0.1

    @classmethod
    def get_user_scores(
        cls,
        user_id: str,
        position: Optional[str] = None,
        limit: int = 10,
    ) -> List[ScoreResponse]:
        """获取用户的评分历史"""
        scores = get_collection("scores")

        query = {"user_id": user_id}
        if position:
            query["position"] = position

        cursor = scores.find(query).sort("created_at", -1).limit(limit)

        result = []
        for doc in cursor:
            result.append(ScoreResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                interview_id=doc["interview_id"],
                position=doc["position"],
                total_score=doc["total_score"],
                dimension_scores=DimensionScores(**doc["dimension_scores"]),
                created_at=doc["created_at"],
            ))

        return result

    @classmethod
    def get_radar_chart_data(cls, user_id: str) -> RadarChartData:
        """
        获取雷达图数据（综合评分，时间衰减加权）

        计算公式：
        weight_i = exp(-λ × (current_time - interview_time))
        score_avg = Σ(score_i × weight_i) / Σ(weight_i)
        """
        scores = get_collection("scores")

        # 获取用户所有评分
        cursor = scores.find({"user_id": user_id}).sort("created_at", -1)

        current_time = datetime.utcnow()
        weighted_scores = {
            "technical": [],
            "communication": [],
            "problem_solving": [],
            "experience": [],
            "logical_thinking": [],
        }

        for doc in cursor:
            # 计算时间衰减权重
            time_diff = (current_time - doc["created_at"]).total_seconds() / 3600  # 转换为小时
            weight = math.exp(-cls.DECAY_LAMBDA * time_diff)

            dim_scores = doc.get("dimension_scores", {})

            for key in weighted_scores:
                if key in dim_scores:
                    weighted_scores[key].append({
                        "score": dim_scores[key],
                        "weight": weight,
                    })

        # 计算加权平均
        result = {}
        for key, items in weighted_scores.items():
            if items:
                total_weighted = sum(item["score"] * item["weight"] for item in items)
                total_weight = sum(item["weight"] for item in items)
                result[key] = round(total_weighted / total_weight, 1) if total_weight > 0 else 0.0
            else:
                result[key] = 0.0

        # 归一化到0-100
        for key in result:
            result[key] = min(100.0, max(0.0, result[key]))

        return RadarChartData(
            technical=result["technical"],
            communication=result["communication"],
            problem_solving=result["problem_solving"],
            experience=result["experience"],
            logical_thinking=result["logical_thinking"],
        )

    @classmethod
    def get_score_trend(
        cls,
        user_id: str,
        position: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取评分趋势

        Returns:
            [{"date": ..., "total_score": ..., "dimension_scores": {...}}]
        """
        scores = get_collection("scores")

        query = {"user_id": user_id}
        if position:
            query["position"] = position

        cursor = scores.find(query).sort("created_at", -1).limit(limit)

        trend = []
        for doc in cursor:
            trend.append({
                "date": doc["created_at"].strftime("%Y-%m-%d"),
                "total_score": round(doc["total_score"], 1),
                "dimension_scores": doc.get("dimension_scores", {}),
                "position": doc.get("position", ""),
            })

        return trend

    @classmethod
    def get_average_score_by_position(cls, user_id: str) -> Dict[str, float]:
        """获取用户各岗位的平均分"""
        scores = get_collection("scores")

        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$position",
                "avg_score": {"$avg": "$total_score"},
            }},
        ]

        result = {}
        for doc in scores.aggregate(pipeline):
            result[doc["_id"]] = round(doc["avg_score"], 1)

        return result
