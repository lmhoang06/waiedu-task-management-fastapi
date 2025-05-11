from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from models.schemas import APIResponse
from db import get_db
from models.project import Comment, Task, Project
from utils.jwt import require_admin_user, get_user_from_token
from models.core import User, Role

router = APIRouter(prefix="/comments", tags=["comments"])

bearer_scheme = HTTPBearer()

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentRead(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class CommentUpdate(BaseModel):
    content: Optional[str] = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    user, error = await get_user_from_token(token, db)
    if error:
        return None, error
    return user, None

async def is_admin(user: User, db: AsyncSession):
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalars().first()
    return role and role.name.lower() == "admin"

async def is_project_member(user: User, project_id: int, db: AsyncSession):
    # Check if user is project manager
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    
    if not project:
        return False
    
    if project.manager_id == user.id:
        return True
    
    # Check if user is a member of the project
    stmt = """
    SELECT 1 FROM project_members
    WHERE project_id = :project_id AND user_id = :user_id
    """
    result = await db.execute(stmt, {"project_id": project_id, "user_id": user.id})
    return result.scalar() is not None

async def get_task_project_id(task_id: int, db: AsyncSession):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return None
    return task.project_id

@router.get("/{id}", response_model=APIResponse)
async def get_comment(
    id: int, 
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get the comment
    result = await db.execute(select(Comment).where(Comment.id == id))
    comment = result.scalars().first()
    
    if not comment:
        return {
            "success": False,
            "error": {"code": "COMMENT_NOT_FOUND", "details": f"No comment exists with id {id}."},
            "message": "Comment not found."
        }
    
    # Get the task's project
    project_id = await get_task_project_id(comment.task_id, db)
    if not project_id:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"Task for this comment not found."},
            "message": "Task not found."
        }
    
    # Check permission (admin or project member)
    is_user_admin = await is_admin(user, db)
    is_project_member_user = await is_project_member(user, project_id, db)
    
    if not (is_user_admin or is_project_member_user):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only project members or admins can view comments."},
            "message": "You don't have permission to view this comment."
        }
    
    return {
        "success": True,
        "data": CommentRead.model_validate(comment),
        "message": "Comment retrieved successfully."
    }

@router.patch("/{id}", response_model=APIResponse)
async def update_comment(
    id: int,
    comment_update: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get the comment
    result = await db.execute(select(Comment).where(Comment.id == id))
    comment = result.scalars().first()
    if not comment:
        return {
            "success": False,
            "error": {"code": "COMMENT_NOT_FOUND", "details": f"No comment exists with id {id}."},
            "message": "Comment not found."
        }
    
    # Verify user has permission (only comment author or admin can update)
    is_user_admin = await is_admin(user, db)
    is_comment_author = user.id == comment.user_id
    
    if not (is_user_admin or is_comment_author):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only comment author or admin can update this comment."},
            "message": "You don't have permission to update this comment."
        }
    
    # Validate content
    if comment_update.content is not None and comment_update.content.strip() == "":
        return {
            "success": False,
            "error": {"code": "INVALID_CONTENT", "details": "Comment content cannot be empty."},
            "message": "Comment content cannot be empty."
        }
    
    # Update comment
    update_data = comment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(comment, key, value)
    
    await db.commit()
    await db.refresh(comment)
    
    return {
        "success": True,
        "data": CommentRead.model_validate(comment),
        "message": "Comment updated successfully."
    }

@router.delete("/{id}", response_model=APIResponse)
async def delete_comment(
    id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get the comment
    result = await db.execute(select(Comment).where(Comment.id == id))
    comment = result.scalars().first()
    if not comment:
        return {
            "success": False,
            "error": {"code": "COMMENT_NOT_FOUND", "details": f"No comment exists with id {id}."},
            "message": "Comment not found."
        }
    
    # Verify user has permission (only comment author or admin can delete)
    is_user_admin = await is_admin(user, db)
    is_comment_author = user.id == comment.user_id
    
    if not (is_user_admin or is_comment_author):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only comment author or admin can delete this comment."},
            "message": "You don't have permission to delete this comment."
        }
    
    # Delete comment
    await db.delete(comment)
    await db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "Comment deleted successfully."
    }

# Task-specific comment endpoints
task_router = APIRouter(prefix="/tasks", tags=["comments"])

@task_router.get("/{task_id}/comments", response_model=APIResponse)
async def list_task_comments(
    task_id: int, 
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Check if task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Check permission (admin or project member)
    is_user_admin = await is_admin(user, db)
    is_project_member_user = await is_project_member(user, task.project_id, db)
    
    if not (is_user_admin or is_project_member_user):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only project members or admins can view comments."},
            "message": "You don't have permission to view comments for this task."
        }
    
    # Get comments
    stmt = select(Comment).where(Comment.task_id == task_id)
    result = await db.execute(stmt)
    comments = result.scalars().all()
    
    return {
        "success": True,
        "data": [CommentRead.model_validate(comment) for comment in comments],
        "message": "Task comments retrieved successfully."
    }

@task_router.post("/{task_id}/comments", response_model=APIResponse)
async def create_task_comment(
    task_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Check if task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Check permission (admin or project member)
    is_user_admin = await is_admin(user, db)
    is_project_member_user = await is_project_member(user, task.project_id, db)
    
    if not (is_user_admin or is_project_member_user):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only project members or admins can create comments."},
            "message": "You don't have permission to create comments for this task."
        }
    
    # Validate content
    if comment.content.strip() == "":
        return {
            "success": False,
            "error": {"code": "INVALID_CONTENT", "details": "Comment content cannot be empty."},
            "message": "Comment content cannot be empty."
        }
    
    # Create comment
    db_comment = Comment(
        task_id=task_id,
        user_id=user.id,
        content=comment.content
    )
    
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    return {
        "success": True,
        "data": CommentRead.model_validate(db_comment),
        "message": "Comment created successfully."
    } 