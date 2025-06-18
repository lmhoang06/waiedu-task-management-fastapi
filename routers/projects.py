from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from models.schemas import APIResponse, ErrorDetail
from db import get_db
from models.project import Project, ProjectMember
from utils.jwt import require_admin_user, get_user_from_token
from models.core import User, Role
from models.enums import ProjectStatusEnum

router = APIRouter(prefix="/projects", tags=["projects"])

bearer_scheme = HTTPBearer()

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    manager_id: Optional[int] = None
    budget: Optional[int] = 0
    priority: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    manager_id: Optional[int] = None
    budget: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class ProjectStatusUpdate(BaseModel):
    status: str

class ProjectMemberBase(BaseModel):
    user_id: int
    role: str

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberRead(ProjectMemberBase):
    id: int
    project_id: int
    joined_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

async def get_current_user(db: AsyncSession = Depends(get_db), credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    token = credentials.credentials
    user, error = await get_user_from_token(token, db)
    if error:
        return None, error
    return user, None

async def is_admin(user: User, db: AsyncSession):
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalars().first()
    return role and role.name.lower() == "admin"

async def is_project_manager(user: User, project: Project):
    """Check if user is the manager of the specified project."""
    return user.id == project.manager_id

@router.get("", response_model=APIResponse)
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    return {
        "success": True,
        "data": [ProjectRead.model_validate(project) for project in projects],
        "message": "Projects retrieved successfully."
    }

@router.post("", response_model=APIResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get project data and filter out fields
    project_data = project.model_dump(exclude={"manager_id"})
    
    # Protect timestamp fields
    protected_fields = {"created_at", "updated_at"}
    project_data = {k: v for k, v in project_data.items() if k not in protected_fields}
    
    db_project = Project(**project_data, manager_id=user.id, status=ProjectStatusEnum.pending_approval.value)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return {
        "success": True,
        "data": ProjectRead.model_validate(db_project),
        "message": "Project created successfully."
    }

@router.get("/{project_id}", response_model=APIResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    return {
        "success": True,
        "data": ProjectRead.model_validate(project),
        "message": "Project retrieved successfully."
    }

@router.patch("/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    admin = await is_admin(user, db)
    # Check if user is the manager of this specific project
    manager = await is_project_manager(user, project)
    
    # Get update data and filter out fields that don't exist in the model
    update_data = project_update.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in update_data.items() if hasattr(project, k)}
    
    # Protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    update_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    # If user is manager but not admin, restrict updating certain fields
    if manager and not admin:
        restricted_fields = {"manager_id", "priority", "budget"}
        # Remove restricted fields from update data
        for field in restricted_fields:
            if field in update_data:
                update_data.pop(field)
    
    # Handle status update with permission and transition logic
    if "status" in update_data:
        new_status = update_data.pop("status")
        allowed_admin_statuses = {"approve": ProjectStatusEnum.in_progress.value, "reject": ProjectStatusEnum.rejected.value, "cancel": ProjectStatusEnum.cancelled.value, "on_hold": ProjectStatusEnum.on_hold.value}
        if new_status == "completed":
            if not (admin or manager):
                return {
                    "success": False,
                    "error": ErrorDetail(code="FORBIDDEN", details="Only admin or this project's manager can set completed."),
                    "message": "You do not have permission to complete this project."
                }
            project.status = ProjectStatusEnum.completed.value
        elif new_status in allowed_admin_statuses:
            if not admin:
                return {
                    "success": False,
                    "error": ErrorDetail(code="FORBIDDEN", details=f"Only admin can set status to {new_status}."),
                    "message": f"Only admin can set status to {new_status}."
                }
            project.status = allowed_admin_statuses[new_status]
        else:
            return {
                "success": False,
                "error": ErrorDetail(code="INVALID_STATUS", details=f"Invalid status update: {new_status}"),
                "message": f"Invalid status update: {new_status}"
            }
    # Handle other fields update
    if not (admin or manager):
        return {
            "success": False,
            "error": ErrorDetail(code="FORBIDDEN", details="Only admin or this project's manager can update this project."),
            "message": "You do not have permission to update this project."
        }
    for key, value in update_data.items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return {
        "success": True,
        "data": ProjectRead.model_validate(project),
        "message": "Project updated successfully."
    }

@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    admin = await is_admin(user, db)
    if not admin:
        return {
            "success": False,
            "error": ErrorDetail(code="FORBIDDEN", details="Only admin can delete a project."),
            "message": "You do not have permission to delete this project."
        }
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    await db.delete(project)
    await db.commit()
    return {
        "success": True,
        "message": "Project deleted successfully."
    }

@router.get("/{project_id}/members", response_model=APIResponse)
async def list_project_members(
    project_id: int, 
    db: AsyncSession = Depends(get_db)
):
    # Check if project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    
    # Get all members for this project
    result = await db.execute(select(ProjectMember).where(ProjectMember.project_id == project_id))
    members = result.scalars().all()
    
    return {
        "success": True,
        "data": [ProjectMemberRead.model_validate(member) for member in members],
        "message": "Project members retrieved successfully."
    }

@router.post("/{project_id}/members", response_model=APIResponse)
async def add_project_member(
    project_id: int,
    member: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Get member data
    member_data = member.model_dump()
    
    # Protect timestamp fields
    protected_fields = {"joined_at"}
    member_data = {k: v for k, v in member_data.items() if k not in protected_fields}
    
    # Check if project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    
    # Check if user has permission (admin or this project's manager)
    admin = await is_admin(user, db)
    manager = await is_project_manager(user, project)
    if not (admin or manager):
        return {
            "success": False,
            "error": ErrorDetail(code="FORBIDDEN", details="Only admin or this project's manager can add members."),
            "message": "You do not have permission to add members to this project."
        }
    
    # Check if the user to be added exists
    result = await db.execute(select(User).where(User.id == member_data["user_id"]))
    user_to_add = result.scalars().first()
    if not user_to_add:
        return {
            "success": False,
            "error": ErrorDetail(code="USER_NOT_FOUND", details=f"No user exists with id {member_data['user_id']}."),
            "message": "User not found."
        }
    
    # Check if user is already a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_data["user_id"]
        )
    )
    existing_member = result.scalars().first()
    if existing_member:
        return {
            "success": False,
            "error": ErrorDetail(code="ALREADY_MEMBER", details=f"User {member_data['user_id']} is already a member of project {project_id}."),
            "message": "User is already a member of the project."
        }
    
    # Add the new member
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data["user_id"],
        role=member_data["role"]
    )
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    
    return {
        "success": True,
        "data": ProjectMemberRead.model_validate(db_member),
        "message": "Member added to project successfully."
    }

@router.delete("/{project_id}/members/{user_id}", response_model=APIResponse)
async def remove_project_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Check if project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        return {
            "success": False,
            "error": ErrorDetail(code="PROJECT_NOT_FOUND", details=f"No project exists with id {project_id}."),
            "message": "Project not found."
        }
    
    # Check if user has permission (admin or this project's manager)
    admin = await is_admin(user, db)
    manager = await is_project_manager(user, project)
    if not (admin or manager):
        return {
            "success": False,
            "error": ErrorDetail(code="FORBIDDEN", details="Only admin or this project's manager can remove members."),
            "message": "You do not have permission to remove members from this project."
        }
    
    # Check if the member exists
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    )
    member = result.scalars().first()
    if not member:
        return {
            "success": False,
            "error": ErrorDetail(code="MEMBER_NOT_FOUND", details=f"User {user_id} is not a member of project {project_id}."),
            "message": "User is not a member of the project."
        }
    
    # Prevent removing the project manager if they're a member
    if user_id == project.manager_id:
        return {
            "success": False,
            "error": ErrorDetail(code="CANNOT_REMOVE_MANAGER", details="Cannot remove the project manager from the project."),
            "message": "Cannot remove the project manager from the project."
        }
    
    # Remove the member
    await db.delete(member)
    await db.commit()
    
    return {
        "success": True,
        "message": "Member removed from project successfully."
    } 