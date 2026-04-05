"""
面试服务 - 面试流程控制
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
import uuid
import random

from app.config import settings
from app.database import get_collection
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.models.interview import (
    InterviewModel,
    InterviewQuestion,
    InterviewStatus,
)


class InterviewService:
    @staticmethod
    def start_interview(user_id: str, position: str) -> InterviewModel:
        """
        开始一场新的面试

        Args:
            user_id: 用户ID
            position: 岗位类型

        Returns:
            InterviewModel
        """
        interviews = get_collection("interviews")

        # 创建面试记录
        interview_doc = {
            "user_id": user_id,
            "position": position,
            "status": InterviewStatus.IN_PROGRESS.value,
            "questions": [],
            "total_score": None,
            "started_at": datetime.utcnow(),
            "ended_at": None,
        }

        result = interviews.insert_one(interview_doc)
        interview_doc["_id"] = result.inserted_id

        return InterviewModel(
            id=str(interview_doc["_id"]),
            user_id=user_id,
            position=position,
            status=InterviewStatus.IN_PROGRESS,
            questions=[],
            total_score=None,
            started_at=interview_doc["started_at"],
            ended_at=None,
        )

    @staticmethod
    def get_interview(interview_id: str) -> Optional[InterviewModel]:
        """获取面试记录"""
        interviews = get_collection("interviews")

        try:
            doc = interviews.find_one({"_id": ObjectId(interview_id)})
            if doc:
                questions = [
                    InterviewQuestion(
                        question_id=q.get("question_id", ""),
                        question=q.get("question", ""),
                        answer=q.get("answer"),
                        comment=q.get("comment"),
                        score=q.get("score"),
                        technical=q.get("technical"),
                        communication=q.get("communication"),
                        problem_solving=q.get("problem_solving"),
                        experience=q.get("experience"),
                        logical_thinking=q.get("logical_thinking"),
                        is_generated=q.get("is_generated", False),
                        is_personalized=q.get("is_personalized", False),
                        correct_answer=q.get("correct_answer"),
                        kb_id=q.get("kb_id"),
                    )
                    for q in doc.get("questions", [])
                ]

                return InterviewModel(
                    id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    position=doc["position"],
                    status=InterviewStatus(doc["status"]),
                    questions=questions,
                    total_score=doc.get("total_score"),
                    started_at=doc["started_at"],
                    ended_at=doc.get("ended_at"),
                )
        except Exception:
            pass

        return None

    @staticmethod
    def get_next_question(
        interview_id: str,
        user_id: str,
        resume_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取下一个面试问题 - 结合知识库题目和简历个性化

        Args:
            interview_id: 面试ID
            user_id: 用户ID
            resume_content: 简历内容（可选）

        Returns:
            {"question": ..., "question_id": ..., "is_first": bool, "is_finished": bool}
        """
        interview = InterviewService.get_interview(interview_id)
        if not interview:
            return {"error": "面试不存在"}

        if interview.user_id != user_id:
            return {"error": "无权限"}

        if interview.status == InterviewStatus.COMPLETED:
            return {"error": "面试已结束", "is_finished": True}

        question_count = len(interview.questions)
        is_first = question_count == 0

        # 检查是否已达最大题数
        if question_count >= settings.MAX_QUESTIONS_PER_INTERVIEW:
            return {"is_finished": True, "question_count": question_count}

        # 生成开场白（第一个问题需要开场白）
        if is_first:
            opening = InterviewService._generate_opening(interview.position, user_id)
        else:
            opening = ""

        # 获取简历内容（如果没有传入）
        if not resume_content:
            resume_content = InterviewService._get_user_resume_content(user_id)

        # 获取上一轮回答（如果有），用于生成追问
        last_answer = None
        last_question = None
        if interview.questions:
            last_q = interview.questions[-1]
            last_question = last_q.question
            last_answer = last_q.answer

        # 生成问题
        question_id = str(uuid.uuid4())

        # 策略：
        # 1-5题：知识库问答，从题库选
        # 6-10题：简历个性化问答，基于简历生成追问
        # 问题标记：is_personalized = True 表示个性化题目

        question_text = None
        correct_answer = ""
        kb_id = None
        is_generated = False
        is_personalized = False

        # 判断当前是否进入个性化阶段（前5题基于简历）
        is_personalized_phase = question_count < 5

        if is_personalized_phase:
            # 个性化阶段（前5题）：用 LLM 基于简历生成项目追问
            resume_summary = InterviewService._get_user_resume_summary(user_id)
            personalized_q = None

            # 优先用简历摘要生成
            if resume_summary:
                personalized_q = llm_service.generate_personalized_question(
                    position=interview.position,
                    resume_content=resume_summary,
                    last_question=last_question,
                    last_answer=last_answer,
                )

            # 如果失败，尝试用完整简历内容
            if not personalized_q and resume_content:
                personalized_q = llm_service.generate_personalized_question(
                    position=interview.position,
                    resume_content=resume_content,
                    last_question=last_question,
                    last_answer=last_answer,
                )

            # 如果还是失败，强制基于简历生成一个通用项目问题
            if not personalized_q:
                if resume_content:
                    # 用简历内容直接生成项目追问
                    personalized_q = llm_service.generate_personalized_question(
                        position=interview.position,
                        resume_content=resume_content,
                        last_question=None,
                        last_answer=None,
                    )
                elif resume_summary:
                    personalized_q = llm_service.generate_personalized_question(
                        position=interview.position,
                        resume_content=resume_summary,
                        last_question=None,
                        last_answer=None,
                    )

            if personalized_q:
                question_text = personalized_q
                is_generated = True
                is_personalized = True
                correct_answer = ""

        # 如果没有生成个性化问题（后5题），从知识库选
        if not question_text:
            asked_kb_ids = set()
            for q in interview.questions:
                if hasattr(q, 'kb_id') and q.kb_id:
                    asked_kb_ids.add(q.kb_id)

            position_queries = {
                "backend": "Java Python Go 微服务 分布式 缓存 数据库 后端",
                "algorithm": "大模型 LLM RAG LangChain AI Agent 向量 深度学习",
                "network": "网络 TCP IP 路由 交换 安全 协议",
            }
            query_text = position_queries.get(interview.position, f"{interview.position}")

            all_candidates = []
            # 获取大量候选题目，确保多样性
            retrieved_docs = rag_service.retrieve(
                query=query_text,
                position=interview.position,
                top_k=500,
            )
            for doc in retrieved_docs:
                if doc.get("id") not in asked_kb_ids:
                    all_candidates.append(doc)

            if not all_candidates:
                retrieved_docs = rag_service.retrieve(
                    query="技术 面试 题 项目 经验 开发",
                    position=None,
                    top_k=500,
                )
                for doc in retrieved_docs:
                    if doc.get("id") not in asked_kb_ids:
                        all_candidates.append(doc)

            if not all_candidates:
                retrieved_docs = rag_service.retrieve(
                    query="Python Java 编程 代码",
                    position=None,
                    top_k=500,
                )
                for doc in retrieved_docs:
                    if doc.get("id") not in asked_kb_ids:
                        all_candidates.append(doc)

            if not all_candidates:
                return {"error": "题库已问完", "is_finished": True}

            # 充分随机打乱
            random.shuffle(all_candidates)
            # 随机选一个
            selected = random.choice(all_candidates)
            question_text = selected["question"]
            correct_answer = selected["answer"]
            kb_id = selected.get("id", str(uuid.uuid4()))
            is_generated = False
            is_personalized = False

        # 记录问题到面试记录
        interviews = get_collection("interviews")
        interviews.update_one(
            {"_id": ObjectId(interview_id)},
            {
                "$push": {
                    "questions": {
                        "question_id": question_id,
                        "question": question_text,
                        "answer": None,
                        "correct_answer": correct_answer if not is_generated else None,
                        "comment": None,
                        "score": None,
                        "is_generated": is_generated,
                        "is_personalized": is_personalized,
                        "kb_id": kb_id,
                    }
                }
            },
        )

        return {
            "question_id": question_id,
            "question": question_text,
            "opening": opening,
            "is_first": is_first,
            "is_finished": False,
            "question_count": question_count + 1,
            "is_personalized": is_personalized,
        }

    @staticmethod
    def submit_answer(
        interview_id: str,
        user_id: str,
        question_id: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        提交回答

        Args:
            interview_id: 面试ID
            user_id: 用户ID
            question_id: 问题ID
            answer: 回答

        Returns:
            {"comment": ..., "score": ..., "correct_answer": ..., "is_finished": bool}
        """
        interview = InterviewService.get_interview(interview_id)
        if not interview:
            return {"error": "面试不存在"}

        if interview.user_id != user_id:
            return {"error": "无权限"}

        if interview.status == InterviewStatus.COMPLETED:
            return {"error": "面试已结束", "is_finished": True}

        # 找到当前问题
        current_question = None
        for q in interview.questions:
            if q.question_id == question_id:
                current_question = q
                break

        if not current_question:
            return {"error": "问题不存在"}

        # 直接使用存储的标准答案（来自知识库题目）
        correct_answer = current_question.correct_answer if hasattr(current_question, 'correct_answer') else None

        # 生成点评（将标准答案作为上下文）
        context_text = f"标准答案：{correct_answer}" if correct_answer else ""

        comment_result = llm_service.generate_comment(
            question=current_question.question,
            answer=answer,
            context=context_text,
        )

        # 更新面试记录中的回答和点评
        interviews = get_collection("interviews")
        interviews.update_one(
            {
                "_id": ObjectId(interview_id),
                "questions.question_id": question_id,
            },
            {
                "$set": {
                    "questions.$.answer": answer,
                    "questions.$.comment": comment_result["comment"],
                    "questions.$.technical": comment_result.get("technical", 5.0),
                    "questions.$.communication": comment_result.get("communication", 5.0),
                    "questions.$.problem_solving": comment_result.get("problem_solving", 5.0),
                    "questions.$.experience": comment_result.get("experience", 5.0),
                    "questions.$.logical_thinking": comment_result.get("logical_thinking", 5.0),
                }
            },
        )

        question_count = len(interview.questions)
        is_finished = question_count >= settings.MAX_QUESTIONS_PER_INTERVIEW

        # 计算综合分数（5个维度的平均）
        tech = comment_result.get("technical", 5.0)
        comm = comment_result.get("communication", 5.0)
        prob = comment_result.get("problem_solving", 5.0)
        exp = comment_result.get("experience", 5.0)
        logic = comment_result.get("logical_thinking", 5.0)
        avg_score = (tech + comm + prob + exp + logic) / 5

        return {
            "comment": comment_result["comment"],
            "score": avg_score,
            "technical": tech,
            "communication": comm,
            "problem_solving": prob,
            "experience": exp,
            "logical_thinking": logic,
            "correct_answer": correct_answer or "",
            "is_finished": is_finished,
            "question_count": question_count,
        }

    @staticmethod
    def end_interview(interview_id: str, user_id: str) -> Dict[str, Any]:
        """结束面试并计算总分"""
        interview = InterviewService.get_interview(interview_id)
        if not interview:
            return {"error": "面试不存在"}

        if interview.user_id != user_id:
            return {"error": "无权限"}

        if interview.status == InterviewStatus.COMPLETED:
            return {"error": "面试已结束"}

        # 计算总分（5个维度的平均分）
        total_score = 0.0
        dimension_scores = {
            "technical": 0.0,
            "communication": 0.0,
            "problem_solving": 0.0,
            "experience": 0.0,
            "logical_thinking": 0.0,
        }

        scored_questions = [q for q in interview.questions if q.technical is not None or q.score is not None]

        if scored_questions:
            n = len(scored_questions)

            # 每个维度独立计算平均分
            for q in scored_questions:
                # 如果有独立维度分数就用，没有就用总分 fallback
                if q.technical is not None:
                    dimension_scores["technical"] += q.technical
                    dimension_scores["communication"] += getattr(q, 'communication', q.technical)
                    dimension_scores["problem_solving"] += getattr(q, 'problem_solving', q.technical)
                    dimension_scores["experience"] += getattr(q, 'experience', q.technical)
                    dimension_scores["logical_thinking"] += getattr(q, 'logical_thinking', q.technical)
                elif q.score is not None:
                    # fallback: 用总分作为所有维度
                    dimension_scores["technical"] += q.score
                    dimension_scores["communication"] += q.score
                    dimension_scores["problem_solving"] += q.score
                    dimension_scores["experience"] += q.score
                    dimension_scores["logical_thinking"] += q.score

            # 除以题目数量，归一化到 0-10
            for key in dimension_scores:
                dimension_scores[key] = min(dimension_scores[key] / n, 10.0)

            # 总分 = 5个维度的平均值
            total_score = sum(dimension_scores.values()) / 5

        # 更新面试状态
        interviews = get_collection("interviews")
        interviews.update_one(
            {"_id": ObjectId(interview_id)},
            {
                "$set": {
                    "status": InterviewStatus.COMPLETED.value,
                    "total_score": total_score,
                    "ended_at": datetime.utcnow(),
                }
            },
        )

        # 保存评分记录
        scores = get_collection("scores")
        scores.insert_one({
            "user_id": user_id,
            "interview_id": interview_id,
            "position": interview.position,
            "total_score": total_score,
            "dimension_scores": dimension_scores,
            "created_at": datetime.utcnow(),
        })

        # 知识库自进化 - 检查是否有新问题需要添加
        InterviewService._knowledge_base_evolution(interview)

        return {
            "total_score": total_score,
            "dimension_scores": dimension_scores,
            "question_count": len(interview.questions),
        }

    @staticmethod
    def _generate_opening(position: str, user_id: str) -> str:
        """生成面试开场白"""
        openings = {
            "backend": "你好，欢迎参加后端工程师岗位的面试。我是今天的AI面试官，接下来我会向你提问一些关于后端开发的问题，请根据你的真实经验来回答。准备好了吗？让我们开始吧！",
            "algorithm": "你好，欢迎参加大模型应用开发工程师岗位的面试。我是今天的AI面试官，接下来我会向你提问一些关于大模型、LangChain、RAG等的问题，请根据你的真实能力来回答。准备好了吗？让我们开始吧！",
            "network": "你好，欢迎参加网络工程师岗位的面试。我是今天的AI面试官，接下来我会向你提问一些关于网络协议、安全、运维的问题，请根据你的真实经验来回答。准备好了吗？让我们开始吧！",
        }

        return openings.get(position, "你好，欢迎参加面试。我是今天的AI面试官，接下来我会向你提问一些问题，请根据你的真实经验来回答。准备好了吗？让我们开始吧！")

    @staticmethod
    def _get_user_resume_content(user_id: str) -> Optional[str]:
        """获取用户项目经历内容"""
        projects = get_collection("projects")
        project_list = list(projects.find({"user_id": user_id}).sort("created_at", -1))

        if not project_list:
            return None

        parts = []
        for i, proj in enumerate(project_list, 1):
            parts.append(f"项目{i}: {proj.get('name', '')}")
            if proj.get('description'):
                parts.append(f"  描述: {proj.get('description', '')}")
            if proj.get('techs'):
                parts.append(f"  技术栈: {', '.join(proj.get('techs', []))}")

        return "\n".join(parts)

    @staticmethod
    def _get_user_resume_summary(user_id: str) -> str:
        """获取用户项目经历的摘要（用于生成个性化问题）"""
        projects = get_collection("projects")
        project_list = list(projects.find({"user_id": user_id}).sort("created_at", -1))

        if not project_list:
            return ""

        parts = []
        for i, proj in enumerate(project_list[:3], 1):  # 最多3个项目
            name = proj.get('name', '')
            desc = proj.get('description', '')[:200]
            techs = ', '.join(proj.get('techs', [])[:5])
            parts.append(f"项目{i}: {name}")
            if desc:
                parts.append(f"  {desc}")
            if techs:
                parts.append(f"  技术: {techs}")

        return "\n\n".join(parts) if parts else ""

    @staticmethod
    def _extract_keywords_from_answer(answer: str, resume_content: Optional[str] = None) -> str:
        """从用户回答中提取关键词，用于在知识库中检索相关问题"""
        import re

        # 常见技术关键词
        tech_keywords = [
            "微服务", "分布式", "缓存", "消息队列", "数据库", "MySQL", "PostgreSQL",
            "MongoDB", "Redis", "Docker", "Kubernetes", "K8S", "Spring", "Spring Boot",
            "Flask", "Django", "FastAPI", "LangChain", "RAG", "LLM", "GPT",
            "TensorFlow", "PyTorch", "深度学习", "机器学习", "神经网络",
            "TCP", "UDP", "HTTP", "HTTPS", "WebSocket", "网络协议",
            "架构设计", "高并发", "负载均衡", "容灾", "备份",
            "Java", "Python", "Go", "JavaScript", "TypeScript", "React", "Vue",
        ]

        found = []
        answer_lower = answer.lower()

        for kw in tech_keywords:
            if kw.lower() in answer_lower:
                found.append(kw)

        # 如果简历中有提到但回答中没提取到
        if resume_content:
            resume_lower = resume_content.lower()
            for kw in tech_keywords:
                if kw.lower() in resume_lower and kw not in found:
                    # 优先添加简历中的技能
                    found.insert(0, kw)

        # 返回关键词组合
        return " ".join(found[:8]) if found else answer[:100]

    @staticmethod
    def _knowledge_base_evolution(interview: InterviewModel):
        """
        知识库自进化

        检查面试中LLM生成的新问题，如果质量好则添加到知识库
        """
        generated_questions = [
            q for q in interview.questions
            if q.is_generated and q.score and q.score >= 8.0
        ]

        for q in generated_questions:
            # 检查是否已有相似问题
            is_added = rag_service.add_generated_question(
                question=q.question,
                answer=q.comment or "",
                position=interview.position,
            )

            if is_added:
                print(f"知识库已添加新问题: {q.question[:50]}...")

    @staticmethod
    def delete_interview(interview_id: str, user_id: str) -> bool:
        """
        删除面试记录

        Args:
            interview_id: 面试ID
            user_id: 用户ID

        Returns:
            bool: 是否删除成功
        """
        interviews = get_collection("interviews")

        try:
            # 先查询，确保面试存在且属于该用户
            interview = interviews.find_one({
                "_id": ObjectId(interview_id),
                "user_id": user_id
            })

            if not interview:
                return False

            # 删除面试记录
            interviews.delete_one({"_id": ObjectId(interview_id)})

            # 同时删除关联的评分记录
            scores = get_collection("scores")
            scores.delete_many({"interview_id": interview_id})

            return True
        except Exception as e:
            print(f"删除面试失败: {e}")
            return False
