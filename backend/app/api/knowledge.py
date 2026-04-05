"""
知识库API
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
import os

from app.services import rag_service
from app.vector_db import VectorDB
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.post("/rebuild", response_model=dict)
async def rebuild_knowledge_base(
    current_user: dict = Depends(get_current_user),
):
    """
    重建知识库

    读取knowledge_base目录下的MD文件，构建向量索引
    """
    knowledge_dir = "./knowledge_base"

    if not os.path.exists(knowledge_dir):
        raise HTTPException(status_code=400, detail="知识库目录不存在")

    total_docs = 0

    # 遍历所有MD文件
    for filename in os.listdir(knowledge_dir):
        if not filename.endswith(".md"):
            continue

        # 确定岗位类型
        if 'Java' in filename or '后端' in filename:
            position = 'backend'
        elif '大模型' in filename or 'LLM' in filename or 'AI' in filename:
            position = 'algorithm'
        elif '网络' in filename:
            position = 'network'
        else:
            position = filename.replace(".md", "").replace("_engineer", "")

        file_path = os.path.join(knowledge_dir, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 解析文档
        documents = rag_service.parse_md_to_documents(md_content, position)

        # 添加到知识库
        if documents:
            count = rag_service.add_documents_to_knowledge_base(documents)
            total_docs += count

    return {
        "success": True,
        "message": f"知识库重建完成，共添加 {total_docs} 个文档",
        "total_documents": total_docs,
    }


@router.post("/add", response_model=dict)
async def add_question(
    question: str,
    answer: str,
    position: str,
    tags: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    添加新题目到知识库
    """
    tag_list = tags.split(",") if tags else []

    is_added = rag_service.add_generated_question(
        question=question,
        answer=answer,
        position=position,
        tags=tag_list,
    )

    if is_added:
        return {
            "success": True,
            "message": "题目已添加到知识库",
        }
    else:
        return {
            "success": False,
            "message": "知识库中已存在相似题目，未添加",
        }


@router.get("/search", response_model=dict)
async def search_knowledge(
    query: str,
    position: Optional[str] = None,
    top_k: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """搜索知识库"""
    results = rag_service.retrieve(
        query=query,
        position=position,
        top_k=top_k,
    )

    return {
        "success": True,
        "results": [
            {
                "question": r["question"],
                "answer": r["answer"],
                "tags": r.get("tags", []),
                "position": r.get("position", ""),
                "score": r.get("score", 0),
            }
            for r in results
        ]
    }


@router.post("/reset", response_model=dict)
async def reset_knowledge_base(
    current_user: dict = Depends(get_current_user),
):
    """重置知识库（谨慎使用）"""
    VectorDB.reset()

    return {
        "success": True,
        "message": "知识库已重置",
    }
