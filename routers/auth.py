from fastapi import APIRouter, Depends, status, Header, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional, Union
from passlib.hash import bcrypt
import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.core import User, UserToken
from models.enums import UserStatusEnum
from models.schemas import APIResponse
from db import get_db
from utils.jwt import get_user_from_token, create_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

TOKEN_EXPIRE_HOURS = 24

@router.post("/login", response_model=APIResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Filter to only use expected fields
    login_data = payload.model_dump(exclude_unset=True)
    username = login_data.get("username")
    email = login_data.get("email")
    password = login_data.get("password")
    
    # Must provide either username or email and password
    if not username and not email:
        return {
            "success": False,
            "error": {"code": "MISSING_CREDENTIALS", "details": "Username or email is required."},
            "message": "Username or email is required."
        }
    
    if not password:
        return {
            "success": False,
            "error": {"code": "MISSING_CREDENTIALS", "details": "Password is required."},
            "message": "Password is required."
        }
    
    # Query user by username or email
    query = select(User)
    if username:
        query = query.where(User.username == username)
    else:
        query = query.where(User.email == email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        return {
            "success": False,
            "error": {"code": "USER_NOT_FOUND", "details": "No user found with the provided credentials."},
            "message": "Invalid username/email or password."
        }

    # Check user status
    if user.status != UserStatusEnum.active:
        return {
            "success": False,
            "error": {"code": "USER_NOT_ACTIVE", "details": f"User status is {user.status}."},
            "message": "User account is not active."
        }

    # Verify password
    if not bcrypt.verify(password, user.password):
        return {
            "success": False,
            "error": {"code": "INVALID_PASSWORD", "details": "Password is incorrect."},
            "message": "Invalid username/email or password."
        }

    # Generate JWT access token
    access_token = create_access_token(user, expire_hours=TOKEN_EXPIRE_HOURS)

    # Remove all expired tokens for this user
    await db.execute(
        UserToken.__table__.delete().where(
            (UserToken.user_id == user.id) & (UserToken.expires_at < datetime.datetime.now(datetime.timezone.utc))
        )
    )

    # Always create a new token for this login
    user_token = UserToken(
        user_id=user.id,
        token=access_token,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    )
    db.add(user_token)

    # Update last_login timestamp
    user.last_login = datetime.datetime.now(datetime.timezone.utc)

    # Commit once, after both operations
    await db.commit()

    # Success: return user info and access token
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "avatar": user.avatar,
        "access_token": access_token
    }
    return {
        "success": True,
        "data": user_data,
        "message": "Login successful."
    }

bearer_scheme = HTTPBearer()

@router.post("/logout", response_model=APIResponse)
async def logout(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    # We only need the token from credentials
    token = credentials.credentials
    
    # Verify token and get user
    user, error = await get_user_from_token(token, db)
    if error:
        return error
        
    # Delete the token from the database
    result = await db.execute(select(UserToken).where(UserToken.user_id == user.id, UserToken.token == token))
    user_token = result.scalars().first()
    if user_token:
        await db.delete(user_token)
        await db.commit()
        return {
            "success": True,
            "message": "Logout successful."
        }
    else:
        return {
            "success": False,
            "error": {"code": "TOKEN_NOT_FOUND", "details": "Token not found in database."},
            "message": "Token not found or already logged out."
        }

@router.post("/forgot-password")
async def forgot_password():
    return {"message": "Forgot password endpoint stub"}

@router.post("/reset-password")
async def reset_password():
    return {"message": "Reset password endpoint stub"} 