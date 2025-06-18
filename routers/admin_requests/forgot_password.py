from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from db import get_db
from utils.jwt import require_admin_user
from models.enums import ForgotPasswordRequestEnum
from models.schemas import APIResponse, ErrorDetail
from models.core import ForgotPasswordRequest, User

bearer_scheme = HTTPBearer()

async def admin_required(db=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    user, error = await require_admin_user(token, db)
    if error or not user:
        raise HTTPException(status_code=403, detail=error["message"] if error else "Admin privileges required")
    return user

router = APIRouter(
    prefix="/forgot-password",
    tags=["admin-requests"],
    dependencies=[Depends(admin_required)]
)

class ForgotPasswordRequestModel(BaseModel):
    id: int
    user_id: int
    status: ForgotPasswordRequestEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

@router.get("/", response_model=APIResponse)
async def list_forgot_password_requests(db: AsyncSession = Depends(get_db)):
    """
    List all forgot password requests.

    Admin only. Returns all forgot password requests in the system.
    """
    result = await db.execute(select(ForgotPasswordRequest))
    requests = result.scalars().all()
    
    return APIResponse(
        success=True,
        data=[ForgotPasswordRequestModel.model_validate(req) for req in requests],
        message="Forgot password requests retrieved successfully."
    )

@router.get("/{request_id}", response_model=APIResponse)
async def get_forgot_password_request(request_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get forgot password request detail.

    Admin only. Returns details for a specific forgot password request by ID.
    """
    result = await db.execute(select(ForgotPasswordRequest).where(ForgotPasswordRequest.id == request_id))
    request = result.scalars().first()
    
    if not request:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="REQUEST_NOT_FOUND", details=f"No request exists with id {request_id}."),
            message="Forgot password request not found."
        )
    
    return APIResponse(
        success=True,
        data=ForgotPasswordRequestModel.model_validate(request),
        message="Forgot password request retrieved successfully."
    )

@router.post("/{request_id}/approve", response_model=APIResponse)
async def approve_forgot_password_request(request_id: int, db: AsyncSession = Depends(get_db)):
    """
    Approve a forgot password request.

    Admin only. Approves a pending request and updates the user's password.
    """
    # First check if request exists and is pending
    result = await db.execute(select(ForgotPasswordRequest).where(ForgotPasswordRequest.id == request_id))
    request = result.scalars().first()
    
    if not request:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="REQUEST_NOT_FOUND", details=f"No request exists with id {request_id}."),
            message="Forgot password request not found."
        )
    
    if request.status != ForgotPasswordRequestEnum.pending_approval:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="INVALID_STATE", details=f"Cannot approve request with status: {request.status.value}"),
            message=f"Cannot approve request with status: {request.status.value}"
        )
    
    # Update the request status
    request.status = ForgotPasswordRequestEnum.approved
    
    # Update the user's password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalars().first()
    
    if not user:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="USER_NOT_FOUND", details=f"User with id {request.user_id} not found."),
            message="User not found."
        )
    
    user.password = request.new_password
    
    await db.commit()
    
    return APIResponse(
        success=True,
        data={"id": request_id, "status": request.status.value},
        message=f"Forgot password request {request_id} approved successfully."
    )

@router.post("/{request_id}/reject", response_model=APIResponse)
async def reject_forgot_password_request(request_id: int, db: AsyncSession = Depends(get_db)):
    """
    Reject a forgot password request.

    Admin only. Rejects a pending forgot password request.
    """
    # First check if request exists and is pending
    result = await db.execute(select(ForgotPasswordRequest).where(ForgotPasswordRequest.id == request_id))
    request = result.scalars().first()
    
    if not request:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="REQUEST_NOT_FOUND", details=f"No request exists with id {request_id}."),
            message="Forgot password request not found."
        )
    
    if request.status != ForgotPasswordRequestEnum.pending_approval:
        return APIResponse(
            success=False,
            error=ErrorDetail(code="INVALID_STATE", details=f"Cannot reject request with status: {request.status.value}"),
            message=f"Cannot reject request with status: {request.status.value}"
        )
    
    # Update the request status
    request.status = ForgotPasswordRequestEnum.denied
    
    await db.commit()
    
    return APIResponse(
        success=True,
        data={"id": request_id, "status": request.status.value},
        message=f"Forgot password request {request_id} rejected successfully."
    ) 