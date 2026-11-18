from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import hash_api_key
from app.repositories.database import get_db
from app.repositories.models import ApiKey

# สร้างตัวดึง Bearer Token อัตโนมัติ (ทำให้มีปุ่ม Authorize รูปแม่กุญแจขึ้นบนหน้า Swagger UI)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_virtual_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """
    ตรวจสอบความถูกต้องของ Virtual API Key ที่ส่งมาใน Header 'Authorization: Bearer sk-gw-...'
    - คืนค่าออบเจกต์ ApiKey จากฐานข้อมูล (เพื่อนำไปผูก api_key_id ใน usage_logs)
    - หากคีย์ผิด ถูกระงับ หรือหมดอายุ จะโยน 401/403 ทันที
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected: Bearer <API_KEY>",
        )

    raw_key = credentials.credentials
    hashed_input = hash_api_key(raw_key)

    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed_input))
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key.",
        )

    if not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This API Key has been revoked or deactivated.",
        )

    if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This API Key has expired.",
        )

    return api_key_record