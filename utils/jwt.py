import os
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.core import User, Role
import datetime

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"

async def get_user_from_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, AttributeError):
        return None, {
            "success": False,
            "error": {"code": "INVALID_TOKEN", "details": "Token is invalid or expired."},
            "message": "Invalid or expired token."
        }
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None, {
            "success": False,
            "error": {"code": "USER_NOT_FOUND", "details": "User not found."},
            "message": "User not found."
        }
    return user, None

async def require_admin_user(token: str, db: AsyncSession):
    user, error = await get_user_from_token(token, db)
    if error:
        return None, error
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalars().first()
    if not role or role.name.lower() != "admin":
        return None, {
            "success": False,
            "error": {"code": "FORBIDDEN", "details": "Admin role required."},
            "message": "You do not have permission to perform this action."
        }
    return user, None

def create_access_token(user, expire_hours=24):
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(hours=expire_hours)
    token_payload = {
        "sub": str(user.id),
        "exp": expires_at,
        "iat": now,
        "username": user.username,
        "email": user.email
    }
    return jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM) 