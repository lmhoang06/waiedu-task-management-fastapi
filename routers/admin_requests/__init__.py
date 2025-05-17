from fastapi import APIRouter
from .forgot_password import router as forgot_password_router

router = APIRouter(
    prefix="/admin/requests",
    tags=["admin-requests"]
)

router.include_router(forgot_password_router)

@router.get("")
async def list_all_admin_requests():
    return {"message": "List all admin requests (all types)"} 