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
from models.core import User, UserToken, ForgotPasswordRequest
from models.enums import UserStatusEnum, ForgotPasswordRequestEnum
from models.schemas import APIResponse, ForgotPasswordRequestIn, ErrorDetail
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
    """
    User Login.

    Authenticates a user by validating their credentials.
    Requires either a username or an email, and a password in the request body.
    On successful authentication, returns user details and a JWT access token.

    Request body fields:
    - **username** (str, optional): The user's username. Provide if email is not used.
    - **email** (str, optional): The user's email address. Provide if username is not used.
    - **password** (str): The user's password.
    """
    # Filter to only use expected fields
    login_data = payload.model_dump(exclude_unset=True)
    username = login_data.get("username")
    email = login_data.get("email")
    password = login_data.get("password")
    
    # Must provide either username or email and password
    if not username and not email:
        return APIResponse(success=False, message="Username or email is required.", error=ErrorDetail(code="MISSING_CREDENTIALS", details="Username or email is required."))
    
    if not password:
        return APIResponse(success=False, error=ErrorDetail(code="MISSING_CREDENTIALS", details="Password is required."), message="Password is required.")
    
    # Query user by username or email
    query = select(User)
    if username:
        query = query.where(User.username == username)
    else:
        query = query.where(User.email == email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        return APIResponse(success=False, error=ErrorDetail(code="USER_NOT_FOUND", details="No user found with the provided credentials."), message="Invalid username/email or password.")

    # Check user status
    if user.status != UserStatusEnum.active:
        return APIResponse(success=False, error=ErrorDetail(code="USER_NOT_ACTIVE", details=f"User status is {user.status}."), message="User account is not active.")

    # Verify password
    if not bcrypt.verify(password, user.password):
        return APIResponse(success=False, error=ErrorDetail(code="INVALID_PASSWORD", details="Password is incorrect."), message="Invalid username/email or password.")

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
    return APIResponse(success=True, data=user_data, message="Login successful.")

bearer_scheme = HTTPBearer()

@router.post("/logout", response_model=APIResponse)
async def logout(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    User Logout.

    Invalidates the active session token provided in the Authorization header (Bearer token).
    """
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
        return APIResponse(success=True, message="Logout successful.")
    else:
        return APIResponse(
            success=False, 
            error=ErrorDetail(code="TOKEN_NOT_FOUND", details="Token not found in database."), 
            message="Token not found or already logged out."
        )

@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(payload: ForgotPasswordRequestIn, db: AsyncSession = Depends(get_db)):
    """
    Forgot Password Request.

    Submits a request to change the user's password. This action requires subsequent administrative approval.

    Request body fields:
    - **username** (str, optional): The user's username. Provide if email is not used.
    - **email** (str, optional): The user's email address. Provide if username is not used.
    - **full_name** (str): The user's full name, used for verification.
    - **new_password** (str): The desired new password for the account.
    """
    # Require at least username or email
    if not payload.username and not payload.email:
        return APIResponse(success=False, message="Username or email is required.", error=ErrorDetail(code="MISSING_CREDENTIALS", details="Username or email is required."))

    # Find user by username or email and full_name
    query = select(User)
    if payload.username:
        query = query.where(User.username == payload.username)
    else:
        query = query.where(User.email == payload.email)
    query = query.where(User.full_name == payload.full_name)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        return APIResponse(
            success=False,
            message="User not found with provided information.",
            error=ErrorDetail(code="USER_NOT_FOUND", details="No user found with the provided username/email and full name.")
        )

    # Hash the new password with bcrypt (rounds=12)
    hashed_password = bcrypt.hash(payload.new_password, rounds=12)

    # Create forgot password request
    forgot_request = ForgotPasswordRequest(
        user_id=user.id,
        new_password=hashed_password,
        status=ForgotPasswordRequestEnum.pending_approval
    )
    db.add(forgot_request)
    await db.commit()
    await db.refresh(forgot_request)

    return APIResponse(
        success=True,
        data={"request_id": forgot_request.id, "status": forgot_request.status},
        message="Password reset request submitted and pending admin approval."
    )
