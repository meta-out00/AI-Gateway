from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import decode_access_token
from app.repositories.database import get_db
from app.repositories.models import User

admin_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(admin_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    ตรวจสอบ JWT Token ของแอดมินสำหรับเข้าใช้งาน Control Plane Endpoints
    - คืนค่าออบเจกต์ User (แอดมิน) จากฐานข้อมูล
    - หาก Token ไม่ถูกต้อง หมดอายุ หรือไม่ใช่แอดมิน จะโยน 401/403 ทันที
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected: Bearer <JWT_TOKEN>",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT token.",
        )

    username: str = payload["sub"]
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found or inactive.",
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )

    return user