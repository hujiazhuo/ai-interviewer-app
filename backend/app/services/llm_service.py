"""
DeepSeek LLM 服务
"""
import logging
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL,
            temperature=0.7,
        )

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        对话接口

        Args:
            messages: [{"role": "user", "content": "..."}]
            temperature: 温度参数

        Returns:
            AI回复文本
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))

        self.llm.temperature = temperature
        response = self.llm.invoke(langchain_messages)
        return response.content

    def generate_interview_question(
        self,
        position: str,
        context: str = "",
        resume_content: Optional[str] = None,
    ) -> str:
        """
        生成面试问题

        Args:
            position: 岗位类型
            context: RAG召回的上下文
            resume_content: 简历内容（可选）

        Returns:
            生成的面试问题
        """
        position_labels = {
            "backend": "后端开发",
            "algorithm": "大模型应用开发",
            "network": "网络工程",
        }
        position_label = position_labels.get(position, position)

        system_prompt = f"""你是一个资深的{position_label}岗位AI面试官，擅长针对该岗位进行面试。
你需要根据以下规则生成面试问题：
1. 问题应该考察候选人的专业技能、解决问题的能力和经验
2. 每个问题应该清晰、具体，便于候选人回答
3. 如果提供了参考知识库内容，问题必须基于这些内容来生成
4. 不要询问过于理论化的问题，要注重实践能力
5. 生成的问题应该与{position_label}岗位高度相关

请生成一个面试问题，只需要问题本身，不要包含"参考知识库"等提示语。
"""

        user_content = ""
        if context:
            user_content += f"参考知识库内容：\n{context}\n\n"
        if resume_content:
            user_content += f"候选人简历：\n{resume_content}\n\n"
        user_content += "请根据以上信息生成一个面试问题。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        return self.chat(messages, temperature=0.8)

    def generate_personalized_question(
        self,
        position: str,
        resume_content: str,
        last_question: Optional[str] = None,
        last_answer: Optional[str] = None,
    ) -> Optional[str]:
        """
        生成个性化追问（基于简历和上一轮回答）

        Args:
            position: 岗位类型
            resume_content: 简历内容
            last_question: 上一道问题（可选）
            last_answer: 上一道回答（可选）

        Returns:
            个性化问题，如果生成失败返回None
        """
        position_labels = {
            "backend": "后端开发",
            "algorithm": "大模型应用开发",
            "network": "网络工程",
        }
        position_label = position_labels.get(position, position)

        system_prompt = f"""你是一个资深的{position_label}岗位AI面试官，擅长根据候选人的简历和回答进行深入追问。

面试要求：
1. 每次只问1-2个简短的问题，不要问太多
2. 问题要针对候选人的具体项目经验、技术栈、工作经历
3. 问题要简洁，一句话最好，不要长篇大论
4. 问题要有深度，考察候选人的实际能力

请根据简历内容生成1-2个简短的个性化问题。
只需要输出问题本身，不要其他内容。
如果简历内容不足，返回空字符串。
"""

        user_content = f"候选人简历：\n{resume_content}\n\n"
        if last_question and last_answer:
            user_content += f"面试官提问：{last_question}\n候选人回答：{last_answer}\n\n请生成1-2个简短的追问。"
        else:
            user_content += "请生成1-2个简短的关于候选人项目经验的问题。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            result = self.chat(messages, temperature=0.7)
            logger.debug(f"generate_personalized_question LLM返回: {result}")
            # 如果返回的内容太短或像是拒绝，说明生成失败
            if not result or len(result) < 10 or "无法" in result or "没有" in result[:20]:
                logger.debug(f"个性化问题生成被拒绝，原因: 返回为空或包含拒绝语句")
                return None
            return result
        except Exception as e:
            logger.error(f"生成个性化问题失败: {e}")
            return None

    def generate_comment(
        self,
        question: str,
        answer: str,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        生成点评

        Args:
            question: 问题
            answer: 回答
            context: 参考答案上下文

        Returns:
            {"comment": "点评内容", "score": 分数, "correct_answer": "参考答案"}
        """
        system_prompt = """你是一个专业的AI面试官，负责对候选人的回答进行点评。请慷慨地给分，只要回答有亮点就给高分。

评分标准（每个维度0-10分）：
- 技术能力：问题回答的技术深度、准确性、完整性
- 沟通表达：回答的条理性、表达能力
- 解决问题的能力：分析问题、解决问题的思路
- 项目经验：对项目经验的掌握程度
- 逻辑思维：回答的逻辑性和系统性

请慷慨给分，7-9分是正常水平，有亮点可以给9-10分。

请按以下JSON格式返回（只需要JSON，不要其他内容）：
{
    "comment": "点评内容",
    "technical": 8.5,
    "communication": 8.0,
    "problem_solving": 7.5,
    "experience": 8.0,
    "logical_thinking": 7.5,
    "correct_answer": "参考答案（如果有）"
}
"""

        user_content = f"问题：{question}\n\n候选人回答：{answer}"
        if context:
            user_content += f"\n\n参考标准答案：{context}"

        response_text = self.chat(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            temperature=0.3,
        )

        # 解析JSON响应
        try:
            import json
            # 尝试提取JSON
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "comment": result.get("comment", ""),
                    "technical": result.get("technical", 5.0),
                    "communication": result.get("communication", 5.0),
                    "problem_solving": result.get("problem_solving", 5.0),
                    "experience": result.get("experience", 5.0),
                    "logical_thinking": result.get("logical_thinking", 5.0),
                    "correct_answer": result.get("correct_answer", ""),
                }
        except Exception:
            pass

        return {
            "comment": response_text,
            "technical": 5.0,
            "communication": 5.0,
            "problem_solving": 5.0,
            "experience": 5.0,
            "logical_thinking": 5.0,
            "correct_answer": "",
        }

    def evaluate_resume(self, resume_content: str, position: str) -> Dict[str, Any]:
        """
        评估简历与岗位的匹配度

        Args:
            resume_content: 简历内容
            position: 岗位类型

        Returns:
            {"strengths": [], "weaknesses": [], "suggestions": []}
        """
        system_prompt = f"""你是一个专业的HR，负责评估简历与{position}岗位的匹配度。
请分析简历并给出：
1. 优势（strengths）
2. 不足（weaknesses）
3. 建议（suggestions）

请按以下JSON格式返回（只需要JSON）：
{{
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["建议1", "建议2"]
}}
"""

        response_text = self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": resume_content},
            ],
            temperature=0.3,
        )

        try:
            import json
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        return {
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
        }


# 单例
llm_service = LLMService()
