"""
RAG知识库服务 - 基于Sentence-Transformer Embedding检索
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.database import get_collection

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.documents_cache = []  # 缓存所有文档
        self.documents_embeddings = []  # 缓存所有文档的embedding
        self.cache_initialized = False

    def parse_md_to_documents(self, md_content: str, position: str) -> List[Dict[str, Any]]:
        """
        解析Markdown文档为问答对

        Args:
            md_content: Markdown文件内容
            position: 岗位类型

        Returns:
            [{"question": ..., "answer": ..., "tags": [...]}]
        """
        documents = []
        lines = md_content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 以 ### 开头的行是问题
            if line.startswith("### "):
                question = line[4:].strip()

                # 收集答案
                answer_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith("### ") or next_line.startswith("## "):
                        break
                    if not next_line.startswith("```") and not next_line.startswith("**答案"):
                        answer_lines.append(next_line)
                    j += 1

                answer = "\n".join(answer_lines).strip()

                if question and answer:
                    tags = self._extract_tags(question + " " + answer)
                    documents.append({
                        "question": question,
                        "answer": answer,
                        "tags": tags,
                        "position": position,
                        "id": str(uuid.uuid4()),
                    })

                i = j
            else:
                i += 1

        return documents

    def _extract_tags(self, text: str) -> List[str]:
        """提取技能标签"""
        common_tags = [
            "Python", "JavaScript", "TypeScript", "React", "Vue", "Node.js",
            "SQL", "MongoDB", "PostgreSQL", "Redis", "Docker", "Kubernetes",
            "Git", "Linux", "AWS", "Azure", "GCP", "RESTful", "GraphQL",
            "微服务", "分布式", "缓存", "消息队列", "算法", "数据结构",
            "系统设计", "设计模式", "前端", "后端", "全栈", "DevOps",
            "Java", "Spring", "FastAPI", "Spring Boot",
            "LangChain", "LangGraph", "AI", "LLM", "RAG", "向量数据库",
            "Transformer", "Attention", "BERT", "GPT",
            "TCP", "UDP", "HTTP", "HTTPS", "DNS", "OSI",
            "交换机", "路由器", "网关", "VLAN", "IP地址",
        ]

        found_tags = []
        text_upper = text.upper()
        for tag in common_tags:
            if tag.upper() in text_upper:
                found_tags.append(tag)

        return found_tags[:5]

    def add_documents_to_knowledge_base(
        self,
        documents: List[Dict[str, Any]],
    ) -> int:
        """
        添加文档到知识库（存储在MongoDB）

        Args:
            documents: [{"question": ..., "answer": ..., "tags": [...], "position": ...}]

        Returns:
            添加的文档数量
        """
        if not documents:
            return 0

        kb_collection = get_collection("knowledge_base")

        # 添加到MongoDB
        for doc in documents:
            kb_collection.update_one(
                {"question": doc["question"]},
                {"$set": doc},
                upsert=True
            )

        # 清除缓存，强制重新加载
        self.cache_initialized = False

        return len(documents)

    def _load_documents(self):
        """加载所有文档到缓存并计算embedding"""
        if self.cache_initialized:
            return

        kb_collection = get_collection("knowledge_base")
        cursor = kb_collection.find({})

        self.documents_cache = []
        texts = []
        for doc in cursor:
            doc_data = {
                "question": doc.get("question", ""),
                "answer": doc.get("answer", ""),
                "tags": doc.get("tags", []),
                "position": doc.get("position", ""),
                "id": doc.get("id", str(doc["_id"])),
            }
            self.documents_cache.append(doc_data)
            texts.append(f"{doc_data['question']} {doc_data['answer']}")

        # 批量计算所有文档的embedding
        if texts:
            self.documents_embeddings = self.model.encode(texts, convert_to_numpy=True)
        else:
            self.documents_embeddings = np.array([])

        self.cache_initialized = True

    def retrieve(
        self,
        query: str,
        position: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        基于Embedding的语义检索

        Args:
            query: 查询文本
            position: 岗位类型筛选
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        self._load_documents()

        if not self.documents_cache:
            return []

        # 过滤岗位
        docs = self.documents_cache
        if position:
            docs = [d for d in docs if d.get("position") == position]

        if not docs:
            return []

        # 找到过滤后文档在原始列表中的索引
        filtered_indices = [i for i, d in enumerate(self.documents_cache) if position is None or d.get("position") == position]

        try:
            # 计算query的embedding
            query_emb = self.model.encode([query], convert_to_numpy=True)

            # 获取过滤后文档的embeddings
            filtered_embeddings = self.documents_embeddings[filtered_indices]

            # 计算余弦相似度
            similarities = cosine_similarity(query_emb, filtered_embeddings).flatten()

            # 构建结果
            results = []
            for i, sim in enumerate(similarities):
                if sim > 0.1:  # 相似度阈值
                    doc = docs[i]
                    results.append({
                        "question": doc["question"],
                        "answer": doc["answer"],
                        "tags": doc.get("tags", []),
                        "position": doc.get("position", ""),
                        "score": float(sim),
                        "id": doc.get("id"),
                    })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def check_similarity(
        self,
        question1: str,
        question2: str,
        threshold: float = 0.85,
    ) -> Tuple[bool, float]:
        """
        检查两个问题的相似度（基于Embedding）
        """
        try:
            emb = self.model.encode([question1, question2], convert_to_numpy=True)
            similarity = cosine_similarity([emb[0]], [emb[1]])[0][0]
            return similarity >= threshold, float(similarity)
        except Exception:
            return False, 0.0

    def add_generated_question(
        self,
        question: str,
        answer: str,
        position: str,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        添加LLM生成的新题目到知识库
        """
        # 检查是否已有相似问题
        self._load_documents()

        for doc in self.documents_cache:
            if doc.get("position") == position:
                is_similar, _ = self.check_similarity(question, doc["question"])
                if is_similar:
                    return False

        doc = {
            "question": question,
            "answer": answer,
            "tags": tags or [],
            "position": position,
            "id": str(uuid.uuid4()),
        }

        self.add_documents_to_knowledge_base([doc])
        return True


# 单例
rag_service = RAGService()
