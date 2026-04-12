"""
RAG知识库服务 - 基于Sentence-Transformer Embedding检索
"""
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
import uuid
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.database import get_collection

# 需在 sentence_transformers 导入前设置，才能让 huggingface_hub 使用镜像
os.environ.setdefault("HF_ENDPOINT", settings.HUGGINGFACE_ENDPOINT)
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RAGService:
    def _resolve_model_from_hub_cache(self, model_id: str) -> Optional[str]:
        cache_root = settings.HUGGINGFACE_HUB_CACHE_DIR
        repo_dir = os.path.join(cache_root, f"models--{model_id.replace('/', '--')}")
        if not os.path.isdir(repo_dir):
            return None

        refs_main = os.path.join(repo_dir, "refs", "main")
        if os.path.isfile(refs_main):
            with open(refs_main, "r", encoding="utf-8") as f:
                snapshot_id = f.read().strip()
            snapshot_dir = os.path.join(repo_dir, "snapshots", snapshot_id)
            if os.path.isdir(snapshot_dir):
                return snapshot_dir

        snapshots_dir = os.path.join(repo_dir, "snapshots")
        if not os.path.isdir(snapshots_dir):
            return None

        candidates = [
            os.path.join(snapshots_dir, d)
            for d in os.listdir(snapshots_dir)
            if os.path.isdir(os.path.join(snapshots_dir, d))
        ]
        if not candidates:
            return None

        candidates.sort(key=os.path.getmtime, reverse=True)
        return candidates[0]

    def __init__(self):
        local_model_dir = settings.HUGGINGFACE_MODEL_LOCAL_DIR
        model_source = settings.HUGGINGFACE_EMBEDDING_MODEL
        hub_snapshot_dir = self._resolve_model_from_hub_cache(model_source)

        if os.path.isdir(local_model_dir):
            logger.info(f"Using local embedding model from {local_model_dir}")
            model_source = local_model_dir
        elif hub_snapshot_dir:
            logger.info(f"Using hub cache embedding model from {hub_snapshot_dir}")
            model_source = hub_snapshot_dir
        elif settings.HUGGINGFACE_LOCAL_ONLY:
            raise RuntimeError(
                "Local-only mode enabled, but no local model found in configured paths"
            )

        try:
            self.model = SentenceTransformer(
                model_source,
                local_files_only=settings.HUGGINGFACE_LOCAL_ONLY,
            )
        except Exception as e:
            logger.warning(f"Embedding model load failed, fallback to keyword retrieval: {e}")
            self.model = None

        self.documents_cache = []  # 缓存所有文档
        self.documents_embeddings = []  # 缓存所有文档的embedding
        self.cache_initialized = False

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """简单关键词相似度，作为离线兜底策略"""
        tokens1 = set(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text1.lower()))
        tokens2 = set(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text2.lower()))

        if not tokens1 or not tokens2:
            return 0.0

        overlap = len(tokens1 & tokens2)
        return overlap / max(len(tokens1), len(tokens2))

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

        # 批量计算所有文档的embedding（模型不可用时走关键词兜底）
        if texts and self.model is not None:
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
            if self.model is None or self.documents_embeddings.size == 0:
                fallback_results = []
                for doc in docs:
                    score = self._keyword_similarity(query, f"{doc['question']} {doc['answer']}")
                    if score > 0.05:
                        fallback_results.append({
                            "question": doc["question"],
                            "answer": doc["answer"],
                            "tags": doc.get("tags", []),
                            "position": doc.get("position", ""),
                            "score": float(score),
                            "id": doc.get("id"),
                        })
                fallback_results.sort(key=lambda x: x["score"], reverse=True)
                return fallback_results[:top_k]

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
            if self.model is None:
                similarity = self._keyword_similarity(question1, question2)
                return similarity >= threshold, float(similarity)

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
