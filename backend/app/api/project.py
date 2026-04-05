"""
项目经历API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_collection
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/project", tags=["项目经历"])


class Project(BaseModel):
    name: str
    description: str
    techs: List[str] = []


@router.get("/list", response_model=dict)
async def list_projects(
    current_user: dict = Depends(get_current_user),
):
    """获取用户的所有项目经历"""
    user_id = current_user["sub"]

    projects = get_collection("projects")
    project_list = list(projects.find({"user_id": user_id}).sort("created_at", -1))

    return {
        "success": True,
        "projects": [
            {
                "name": p.get("name", ""),
                "description": p.get("description", ""),
                "techs": p.get("techs", []),
            }
            for p in project_list
        ]
    }


@router.post("/add", response_model=dict)
async def add_project(
    project: Project,
    current_user: dict = Depends(get_current_user),
):
    """添加项目经历"""
    user_id = current_user["sub"]

    projects = get_collection("projects")
    projects.insert_one({
        "user_id": user_id,
        "name": project.name,
        "description": project.description,
        "techs": project.techs,
        "created_at": None,  # MongoDB会自动添加时间戳
    })

    return {"success": True}


@router.delete("/{index}", response_model=dict)
async def delete_project(
    index: int,
    current_user: dict = Depends(get_current_user),
):
    """删除项目经历（按索引删除最新添加的）"""
    user_id = current_user["sub"]

    projects = get_collection("projects")
    project_list = list(projects.find({"user_id": user_id}).sort("created_at", -1))

    if index < 0 or index >= len(project_list):
        raise HTTPException(status_code=404, detail="项目不存在")

    # 删除指定索引的项目
    target_project = project_list[index]
    projects.delete_one({"_id": target_project["_id"]})

    return {"success": True}


@router.put("/{index}", response_model=dict)
async def update_project(
    index: int,
    project: Project,
    current_user: dict = Depends(get_current_user),
):
    """更新项目经历"""
    user_id = current_user["sub"]

    projects = get_collection("projects")
    project_list = list(projects.find({"user_id": user_id}).sort("created_at", -1))

    if index < 0 or index >= len(project_list):
        raise HTTPException(status_code=404, detail="项目不存在")

    # 更新指定索引的项目
    target_project = project_list[index]
    projects.update_one(
        {"_id": target_project["_id"]},
        {"$set": {
            "name": project.name,
            "description": project.description,
            "techs": project.techs,
        }}
    )

    return {"success": True}
