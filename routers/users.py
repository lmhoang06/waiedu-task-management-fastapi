from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any, Union, Annotated
from pydantic import BaseModel, Field, StringConstraints
from datetime import datetime
from passlib.hash import bcrypt
from models.schemas import APIResponse, ErrorDetail
from db import get_db
from models.core import User, Role
from models.enums import UserStatusEnum
from utils.jwt import get_user_from_token, require_admin_user

router = APIRouter(prefix="/users", tags=["users"])

bearer_scheme = HTTPBearer()

# Email regex pattern
EMAIL_REGEX = r"(?:[a-z0-9!#$%&''*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&''*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"

# Type for email validation
EmailStr = Annotated[str, StringConstraints(pattern=EMAIL_REGEX)]

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=63)
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    full_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(UserStatusEnum.pending_approval.value, description="User status")
    role_id: int = Field(..., gt=0)
    avatar: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=63)
    email: Optional[EmailStr] = Field(None, description="User email address", examples=["user@example.com"])
    full_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    role_id: Optional[int] = Field(None, gt=0)
    password: Optional[str] = Field(None, min_length=8)
    avatar: Optional[str] = Field(None, max_length=255)

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = Field(None, description="User email address", examples=["user@example.com"])
    avatar: Optional[str] = Field(None, max_length=255)
    
@router.get("", response_model=APIResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    List Users.

    Retrieves a list of all users in the system.
    Requires authentication.
    """
    user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    return {
        "success": True,
        "data": [UserRead.model_validate(user) for user in users],
        "message": "Users retrieved successfully."
    }

@router.post("", response_model=APIResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Create User.

    Creates a new user in the system. Requires administrator privileges.
    The user's status will be set to 'active' upon creation by an admin.

    Request body fields (from UserCreate model):
    - **username** (str): Unique username (3-63 characters).
    - **email** (EmailStr): Unique email address.
    - **full_name** (str, optional): User's full name (max 255 characters).
    - **status** (str, optional): User status (e.g., 'active', 'pending_approval'). Defaults to 'pending_approval' if not set by admin, admin creation defaults to 'active'.
    - **role_id** (int): ID of the role to assign to the user.
    - **avatar** (str, optional): URL to the user's avatar image (max 255 characters).
    - **password** (str): User's password (min 8 characters).
    """
    admin, error = await require_admin_user(credentials.credentials, db)
    if error:
        return error
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        return {
            "success": False,
            "error": ErrorDetail(code="USERNAME_EXISTS", details="Username already exists."),
            "message": "Username already exists."
        }
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        return {
            "success": False,
            "error": ErrorDetail(code="EMAIL_EXISTS", details="Email already exists."),
            "message": "Email already exists."
        }
    
    # Verify role exists
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    if not result.scalars().first():
        return {
            "success": False,
            "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {user.role_id}."),
            "message": "Role not found."
        }
    
    # Set status to active when created by admin
    user_status = UserStatusEnum.active.value
    
    # Validate status if provided
    if user.status != UserStatusEnum.active.value and user.status is not None:
        if user.status not in [e.value for e in UserStatusEnum]:
            return {
                "success": False,
                "error": ErrorDetail(code="INVALID_STATUS", details=f"Invalid status: {user.status}"),
                "message": f"Invalid status: {user.status}"
            }
        user_status = user.status
    
    # Hash password
    hashed_password = bcrypt.hash(user.password, rounds=12)
    
    # Create user
    user_data = user.model_dump()
    user_data.pop("password")  # Remove password from dict
    user_data["status"] = user_status  # Set status
    db_user = User(**user_data, password=hashed_password)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return {
        "success": True,
        "data": UserRead.model_validate(db_user),
        "message": "User created successfully."
    }

@router.get("/{id}", response_model=APIResponse)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Get User by ID.

    Retrieves detailed information for a specific user by their ID.
    Any authenticated user can access this endpoint.

    Path parameters:
    - **id** (int): The ID of the user to retrieve.
    """
    current_user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Any authenticated user can view user details
    
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    
    if not user:
        return {
            "success": False,
            "error": ErrorDetail(code="USER_NOT_FOUND", details=f"No user exists with id {id}."),
            "message": "User not found."
        }
    
    return {
        "success": True,
        "data": UserRead.model_validate(user),
        "message": "User retrieved successfully."
    }

@router.patch("/{id}", response_model=APIResponse)
async def update_user(
    id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Update User.

    Updates specified fields for a user. 
    Administrators can update any user. Regular users can only update their own profiles.
    Attempting to update protected fields (e.g., timestamps) will be ignored.

    Path parameters:
    - **id** (int): The ID of the user to update.

    Request body fields (from UserUpdate model, all optional):
    - **username** (str): New username (3-63 characters).
    - **email** (EmailStr): New email address.
    - **full_name** (str): New full name (max 255 characters).
    - **status** (str): New user status (admin only).
    - **role_id** (int): New role ID (admin only).
    - **password** (str): New password (min 8 characters).
    - **avatar** (str): New URL to avatar image (max 255 characters).
    """
    current_user, error = await get_user_from_token(credentials.credentials, db)
    if error:
        return error
    
    # Check if user is admin
    is_admin = False
    result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = result.scalars().first()
    if role and role.name.lower() == "admin":
        is_admin = True
    
    # Get the user to update
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    if not user:
        return {
            "success": False,
            "error": ErrorDetail(code="USER_NOT_FOUND", details=f"No user exists with id {id}."),
            "message": "User not found."
        }
    
    # Only admin can update other users, regular users can only update themselves
    if not is_admin and current_user.id != id:
        return {
            "success": False,
            "error": ErrorDetail(code="FORBIDDEN", details="You can only update your own profile."),
            "message": "You can only update your own profile."
        }
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Filter out any fields that don't exist in the User model
    update_data = {k: v for k, v in update_data.items() if hasattr(user, k)}
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    update_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    # If not admin, further restrict which fields can be updated
    if not is_admin:
        allowed_fields = {"full_name", "email", "avatar", "password", "username"}
        # Silently filter out restricted fields instead of raising an error
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    # Continue with validation only if there are fields to update
    if not update_data:
        return {
            "success": True,
            "message": "No fields to update."
        }
    
    # Validate updates
    # Check username uniqueness if being updated
    if "username" in update_data and update_data["username"] != user.username:
        result = await db.execute(select(User).where(User.username == update_data["username"]))
        if result.scalars().first():
            return {
                "success": False,
                "error": ErrorDetail(code="USERNAME_EXISTS", details="Username already exists."),
                "message": "Username already exists."
            }
    
    # Check email uniqueness if being updated
    if "email" in update_data and update_data["email"] != user.email:
        result = await db.execute(select(User).where(User.email == update_data["email"]))
        if result.scalars().first():
            return {
                "success": False,
                "error": ErrorDetail(code="EMAIL_EXISTS", details="Email already exists."),
                "message": "Email already exists."
            }
    
    # Verify role exists if being updated
    if "role_id" in update_data:
        result = await db.execute(select(Role).where(Role.id == update_data["role_id"]))
        if not result.scalars().first():
            return {
                "success": False,
                "error": ErrorDetail(code="ROLE_NOT_FOUND", details=f"No role exists with id {update_data['role_id']}."),
                "message": "Role not found."
            }
    
    # Validate status if being updated
    if "status" in update_data:
        if update_data["status"] not in [e.value for e in UserStatusEnum]:
            return {
                "success": False,
                "error": ErrorDetail(code="INVALID_STATUS", details=f"Invalid status: {update_data['status']}"),
                "message": f"Invalid status: {update_data['status']}"
            }
    
    # Hash password if being updated
    if "password" in update_data:
        update_data["password"] = bcrypt.hash(update_data["password"], rounds=12)
    
    # Update user
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "data": UserRead.model_validate(user),
        "message": "User updated successfully."
    }

@router.delete("/{id}", response_model=APIResponse)
async def delete_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Deactivate User.

    Marks a user as 'inactive' (soft delete). Requires administrator privileges.
    The user is not permanently removed from the database.

    Path parameters:
    - **id** (int): The ID of the user to deactivate.
    """
    admin, error = await require_admin_user(credentials.credentials, db)
    if error:
        return error
    
    # Get the user
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()
    if not user:
        return {
            "success": False,
            "error": ErrorDetail(code="USER_NOT_FOUND", details=f"No user exists with id {id}."),
            "message": "User not found."
        }
    
    # Soft delete: mark user as inactive instead of deleting
    user.status = UserStatusEnum.inactive.value
    await db.commit()
    
    return {
        "success": True,
        "message": "User deactivated successfully."
    } 