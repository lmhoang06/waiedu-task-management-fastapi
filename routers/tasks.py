from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from models.schemas import APIResponse
from db import get_db
from models.project import Task, TaskAssignment, Project
from utils.jwt import require_admin_user, get_user_from_token
from models.core import User, Role
from models.enums import TaskStatusEnum, PriorityEnum

router = APIRouter(prefix="/tasks", tags=["tasks"])

bearer_scheme = HTTPBearer()

class TaskBase(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    priority: str = 'medium'
    due_date: datetime

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id: int
    status: str
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class TaskUpdate(BaseModel):
    project_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskAssignmentBase(BaseModel):
    user_id: int

class TaskAssignmentCreate(TaskAssignmentBase):
    pass

class TaskAssignmentRead(TaskAssignmentBase):
    id: int
    task_id: int
    assigned_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

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
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
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

@router.get("", response_model=APIResponse)
async def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Task)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    if status:
        if status not in [e.value for e in TaskStatusEnum]:
            return {
                "success": False,
                "error": {"code": "INVALID_STATUS", "details": f"Invalid status: {status}"},
                "message": f"Invalid status filter: {status}"
            }
        query = query.where(Task.status == status)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return {
        "success": True,
        "data": [TaskRead.model_validate(task) for task in tasks],
        "message": "Tasks retrieved successfully."
    }

@router.post("", response_model=APIResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get task data
    task_data = task.model_dump()
    
    # Protect timestamp fields
    protected_fields = {"created_at", "updated_at"}
    task_data = {k: v for k, v in task_data.items() if k not in protected_fields}
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == task.project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": {"code": "PROJECT_NOT_FOUND", "details": f"No project exists with id {task.project_id}."},
            "message": "Project not found."
        }
    
    # Verify user has permission to create task in this project (only admin or project manager)
    is_user_admin = await is_admin(user, db)
    # Verify user is the manager of THIS specific project
    is_project_manager = project.manager_id == user.id
    
    if not (is_user_admin or is_project_manager):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only the project's manager or admins can create tasks."},
            "message": "You don't have permission to create tasks in this project."
        }
    
    # Validate priority
    if task.priority not in [e.value for e in PriorityEnum]:
        return {
            "success": False,
            "error": {"code": "INVALID_PRIORITY", "details": f"Invalid priority: {task.priority}"},
            "message": f"Invalid priority: {task.priority}"
        }
    
    # Create task
    db_task = Task(
        **task_data,
        created_by=user.id,
        status=TaskStatusEnum.todo.value
    )
    
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    return {
        "success": True,
        "data": TaskRead.model_validate(db_task),
        "message": "Task created successfully."
    }

@router.get("/{task_id}", response_model=APIResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    return {
        "success": True,
        "data": TaskRead.model_validate(task),
        "message": "Task retrieved successfully."
    }

@router.patch("/{task_id}", response_model=APIResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get the task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Get update data and filter out fields that don't exist in the model
    update_data = task_update.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in update_data.items() if hasattr(task, k)}
    
    # Protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    update_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    # Special handling for status updates
    if task_update.status is not None:
        # Verify status is valid
        if task_update.status not in [e.value for e in TaskStatusEnum]:
            return {
                "success": False,
                "error": {"code": "INVALID_STATUS", "details": f"Invalid status: {task_update.status}"},
                "message": f"Invalid status: {task_update.status}"
            }
        
        # Check for 'cancelled' status restrictions
        if task_update.status == TaskStatusEnum.cancelled.value:
            # Only admin and project manager can set a task to cancelled
            is_user_admin = await is_admin(user, db)
            
            # Check if user is project manager
            result = await db.execute(select(Project).where(Project.id == task.project_id))
            project = result.scalars().first()
            is_project_manager = project and project.manager_id == user.id
            
            if not (is_user_admin or is_project_manager):
                return {
                    "success": False,
                    "error": {"code": "FORBIDDEN", "details": "Only admin or project manager can cancel a task."},
                    "message": "You don't have permission to cancel this task."
                }
        
        # For any status update, check if user has permission
        # (admin, project manager, or task assignee)
        is_user_admin = await is_admin(user, db) if not locals().get('is_user_admin') else is_user_admin
        
        # Check if project manager
        if not locals().get('project'):
            result = await db.execute(select(Project).where(Project.id == task.project_id))
            project = result.scalars().first()
        is_project_manager = project and project.manager_id == user.id if not locals().get('is_project_manager') else is_project_manager
        
        # Check if user is assigned to this task
        result = await db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.user_id == user.id
            )
        )
        is_task_assignee = result.scalars().first() is not None
        
        if not (is_user_admin or is_project_manager or is_task_assignee):
            return {
                "success": False,
                "error": {"code": "FORBIDDEN", "details": "Only admin, project manager, or assigned users can update task status."},
                "message": "You don't have permission to update this task's status."
            }
    
    # Verify user has permission (only admin or project manager can update tasks)
    is_user_admin = await is_admin(user, db) if not locals().get('is_user_admin') else is_user_admin
    
    # Check if user is the manager of the specific project this task belongs to
    if not locals().get('project'):
        result = await db.execute(select(Project).where(Project.id == task.project_id))
        project = result.scalars().first()
    is_project_manager = project and project.manager_id == user.id if not locals().get('is_project_manager') else is_project_manager
    
    if not (is_user_admin or is_project_manager):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only the project's manager or admins can update tasks."},
            "message": "You don't have permission to update this task."
        }
    
    # If changing project, verify the new project exists and user has access
    if task_update.project_id is not None and task_update.project_id != task.project_id:
        result = await db.execute(select(Project).where(Project.id == task_update.project_id))
        project = result.scalars().first()
        if not project:
            return {
                "success": False,
                "error": {"code": "PROJECT_NOT_FOUND", "details": f"No project exists with id {task_update.project_id}."},
                "message": "Target project not found."
            }
        
        has_project_permission = await is_admin(user, db) or await is_project_member(user, task_update.project_id, db)
        if not has_project_permission:
            return {
                "success": False,
                "error": {"code": "FORBIDDEN", "details": "You don't have permission to move this task to the target project."},
                "message": "You don't have permission to move this task to the target project."
            }
    
    # If updating priority, validate it
    if task_update.priority and task_update.priority not in [e.value for e in PriorityEnum]:
        return {
            "success": False,
            "error": {"code": "INVALID_PRIORITY", "details": f"Invalid priority: {task_update.priority}"},
            "message": f"Invalid priority: {task_update.priority}"
        }
    
    # Update task
    for key, value in update_data.items():
        setattr(task, key, value)
    
    await db.commit()
    await db.refresh(task)
    
    return {
        "success": True,
        "data": TaskRead.model_validate(task),
        "message": "Task updated successfully."
    }

@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get the task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Verify user has permission
    is_user_admin = await is_admin(user, db)
    is_task_creator = user.id == task.created_by
    
    if not (is_user_admin or is_task_creator):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only task creator or admins can delete tasks."},
            "message": "You don't have permission to delete this task."
        }
    
    # Delete task
    await db.delete(task)
    await db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "Task deleted successfully."
    }

@router.get("/{task_id}/assignees", response_model=APIResponse)
async def list_task_assignees(task_id: int, db: AsyncSession = Depends(get_db)):
    # Check if task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Get assignees
    stmt = select(TaskAssignment).where(TaskAssignment.task_id == task_id)
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    
    return {
        "success": True,
        "data": [TaskAssignmentRead.model_validate(assignment) for assignment in assignments],
        "message": "Task assignees retrieved successfully."
    }

@router.post("/{task_id}/assignees", response_model=APIResponse)
async def assign_task(
    task_id: int,
    assignment: TaskAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get assignment data
    assignment_data = assignment.model_dump()
    
    # Protect timestamp fields
    protected_fields = {"assigned_at"}
    assignment_data = {k: v for k, v in assignment_data.items() if k not in protected_fields}
    
    # Check if task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        return {
            "success": False,
            "error": {"code": "TASK_NOT_FOUND", "details": f"No task exists with id {task_id}."},
            "message": "Task not found."
        }
    
    # Verify user has permission
    has_permission = await is_admin(user, db) or user.id == task.created_by or await is_project_member(user, task.project_id, db)
    if not has_permission:
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Only task creator, project members, or admins can assign tasks."},
            "message": "You don't have permission to assign this task."
        }
    
    # Check if user exists
    stmt = select(User).where(User.id == assignment.user_id)
    result = await db.execute(stmt)
    target_user = result.scalars().first()
    if not target_user:
        return {
            "success": False,
            "error": {"code": "USER_NOT_FOUND", "details": f"No user exists with id {assignment.user_id}."},
            "message": "User not found."
        }
    
    # Check if assignment already exists
    stmt = select(TaskAssignment).where(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == assignment.user_id
    )
    result = await db.execute(stmt)
    existing_assignment = result.scalars().first()
    if existing_assignment:
        return {
            "success": False,
            "error": {"code": "ALREADY_ASSIGNED", "details": f"User {assignment.user_id} is already assigned to task {task_id}."},
            "message": "User is already assigned to this task."
        }
    
    # Create assignment
    db_assignment = TaskAssignment(
        task_id=task_id,
        user_id=assignment.user_id
    )
    
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    
    return {
        "success": True,
        "data": TaskAssignmentRead.model_validate(db_assignment),
        "message": "User assigned to task successfully."
    }

@router.delete("/{task_id}/assignees/{user_id}", response_model=APIResponse)
async def unassign_task(
    task_id: int,
    user_id: int,
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
    
    # Verify user has permission (admin, task creator, project member, or the assigned user themselves)
    is_user_admin = await is_admin(user, db)
    is_task_creator = user.id == task.created_by
    is_project_member_user = await is_project_member(user, task.project_id, db)
    is_self_unassign = user.id == user_id
    
    if not (is_user_admin or is_task_creator or is_project_member_user or is_self_unassign):
        return {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "You don't have permission to unassign users from this task."},
            "message": "You don't have permission to unassign users from this task."
        }
    
    # Get the assignment
    stmt = select(TaskAssignment).where(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == user_id
    )
    result = await db.execute(stmt)
    assignment = result.scalars().first()
    
    if not assignment:
        return {
            "success": False,
            "error": {"code": "ASSIGNMENT_NOT_FOUND", "details": f"User {user_id} is not assigned to task {task_id}."},
            "message": "User is not assigned to this task."
        }
    
    # Delete assignment
    await db.delete(assignment)
    await db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "User unassigned from task successfully."
    } 