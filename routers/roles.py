from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from models.schemas import APIResponse, ErrorDetail
from pydantic import BaseModel
from db import get_db
from models.core import Role, User
from utils.jwt import require_admin_user
from datetime import datetime

router = APIRouter(prefix="/roles", tags=["roles"])

bearer_scheme = HTTPBearer()

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[str] = None 

class AssignRoleRequest(BaseModel):
    user_id: int

async def require_admin(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    token = credentials.credentials
    user, error = await require_admin_user(token, db)
    if error:
        return error
    return user

@router.get("", response_model=APIResponse)
async def list_roles(db: AsyncSession = Depends(get_db)):
    """
    List Roles.

    Retrieves a list of all roles available in the system.
    """
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    return {
        "success": True,
        "data": [RoleRead.model_validate(role) for role in roles],
        "message": "Roles retrieved successfully."
    }

@router.post("", response_model=APIResponse)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    """
    Create Role.

    Creates a new role in the system. Requires administrator privileges.

    Request body fields (from RoleCreate model):
    - **name** (str): The name of the role.
    - **description** (str, optional): A description for the role.
    - **permissions** (str, optional): A representation of permissions associated with the role (e.g., JSON string).
    """
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    
    # Filter out fields that don't exist in the model
    role_data = role.model_dump()
    
    # Create a temporary Role object to check attributes 
    temp_role = Role()
    role_data = {k: v for k, v in role_data.items() if hasattr(temp_role, k)}
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    role_data = {k: v for k, v in role_data.items() if k not in protected_fields}
    
    db_role = Role(**role_data)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return {
        "success": True,
        "data": RoleRead.model_validate(db_role),
        "message": "Role created successfully."
    }

@router.get("/{id}", response_model=APIResponse)
async def get_role(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get Role by ID.

    Retrieves detailed information for a specific role by its ID.

    Path parameters:
    - **id** (int): The ID of the role to retrieve.
    """
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalars().first()
    if not role:
        return {
            "success": False,
            "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {id}."),
            "message": "Role not found."
        }
    return {
        "success": True,
        "data": RoleRead.model_validate(role),
        "message": "Role retrieved successfully."
    }

@router.patch("/{id}", response_model=APIResponse)
async def update_role(
    id: int,
    role_update: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    """
    Update Role.

    Updates specified fields for an existing role. Requires administrator privileges.

    Path parameters:
    - **id** (int): The ID of the role to update.

    Request body fields (from RoleUpdate model, all optional):
    - **name** (str): The new name of the role.
    - **description** (str): The new description for the role.
    - **permissions** (str): The new representation of permissions.
    """
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalars().first()
    if not role:
        return {
            "success": False,
            "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {id}."),
            "message": "Role not found."
        }
    
    # Get fields to update and filter out ones that don't exist in the model
    update_data = role_update.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in update_data.items() if hasattr(role, k)}
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    update_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    # If no valid fields to update
    if not update_data:
        return {
            "success": True,
            "message": "No fields to update."
        }
        
    # Update role attributes
    for key, value in update_data.items():
        setattr(role, key, value)
    
    await db.commit()
    await db.refresh(role)
    return {
        "success": True,
        "data": RoleRead.model_validate(role),
        "message": "Role updated successfully."
    }

@router.delete("/{id}", response_model=APIResponse)
async def delete_role(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    """
    Delete Role.

    Deletes a role from the system. Requires administrator privileges.

    Path parameters:
    - **id** (int): The ID of the role to delete.
    """
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalars().first()
    if not role:
        return {
            "success": False,
            "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {id}."),
            "message": "Role not found."
        }
    await db.delete(role)
    await db.commit()
    return {
        "success": True,
        "message": "Role deleted successfully."
    }

@router.post("/{id}/assign", response_model=APIResponse)
async def assign_role(
    id: int,
    payload: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    """
    Assign Role to User.

    Assigns a specified role to a user. Requires administrator privileges.

    Path parameters:
    - **id** (int): The ID of the role to assign.

    Request body fields (from AssignRoleRequest model):
    - **user_id** (int): The ID of the user to whom the role will be assigned.
    """
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    
    # Filter payload to only use the expected fields
    payload_data = payload.model_dump(exclude_unset=True)
    if "user_id" not in payload_data:
        return {
            "success": False,
            "error": ErrorDetail(code="MISSING_FIELD", details="user_id is required"),
            "message": "User ID is required."
        }
    
    user_id = payload_data["user_id"]
    
    # Check if role exists
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalars().first()
    if not role:
        return {
            "success": False,
            "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {id}."),
            "message": "Role not found."
        }
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return {
            "success": False,
            "error": ErrorDetail(code="USER_NOT_FOUND", details=f"No user exists with id {user_id}."),
            "message": "User not found."
        }
    user.role_id = id
    await db.commit()
    await db.refresh(user)
    return {
        "success": True,
        "data": {"user_id": user.id, "role_id": user.role_id},
        "message": f"Role {id} assigned to user {user.id} successfully."
    } 