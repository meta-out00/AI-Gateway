from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.jwt_handler import get_current_admin
from app.auth.security import create_access_token, verify_password
from app.repositories.admin_repo import AdminRepository
from app.repositories.database import get_db
from app.repositories.log_repo import LogRepository
from app.repositories.models import User
from app.schemas.admin_schema import (
    AdminLoginRequest,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyItemResponse,
    ProviderCreateRequest,
    ProviderResponse,
    TokenResponse,
)

router = APIRouter(prefix="/admin", tags=["Control Plane - Admin Management"])


# ==========================================
# 1. เข้าสู่ระบบแอดมิน (ไม่ต้องใช้ JWT)
# ==========================================
@router.post("/login", response_model=TokenResponse)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """ล็อกอินด้วย Username/Password เพื่อรับ JWT Token"""
    admin_repo = AdminRepository(db)
    log_repo = LogRepository(db)
    client_ip = request.client.host if request.client else None

    user = await admin_repo.get_user_by_username(payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        await log_repo.create_audit_log(
            action="ADMIN_LOGIN_FAILED",
            target_resource=f"user:{payload.username}",
            details="Invalid username or password",
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    token = create_access_token(subject=user.username, role=user.role)
    await log_repo.create_audit_log(
        action="ADMIN_LOGIN_SUCCESS",
        target_resource=f"user:{user.username}",
        admin_user_id=user.id,
        ip_address=client_ip,
    )
    return TokenResponse(access_token=token)


# ==========================================
# 2. จัดการ Virtual API Keys (ต้องแนบ Admin JWT)
# ==========================================
@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_virtual_api_key(
    payload: ApiKeyCreateRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """สร้าง Virtual API Key ใหม่ (แสดงคีย์เต็มเพียงครั้งเดียว)"""
    admin_repo = AdminRepository(db)
    log_repo = LogRepository(db)

    new_key, raw_key = await admin_repo.create_api_key(
        key_name=payload.key_name,
        user_id=current_admin.id,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        max_budget_usd=payload.max_budget_usd,
        expires_at=payload.expires_at,
    )

    await log_repo.create_audit_log(
        action="CREATE_API_KEY",
        target_resource=f"api_key:{new_key.id}",
        admin_user_id=current_admin.id,
        details=f"Created key '{new_key.key_name}' ({new_key.key_prefix}), max_budget={new_key.max_budget_usd}",
        ip_address=request.client.host if request.client else None,
    )

    return ApiKeyCreateResponse(
        id=new_key.id,
        key_name=new_key.key_name,
        key_prefix=new_key.key_prefix,
        raw_api_key=raw_key,
        rate_limit_per_minute=new_key.rate_limit_per_minute,
        max_budget_usd=new_key.max_budget_usd,
        current_spend_usd=new_key.current_spend_usd,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyItemResponse])
async def list_virtual_api_keys(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """ดูรายการ Virtual API Keys ทั้งหมดในระบบ"""
    admin_repo = AdminRepository(db)
    return await admin_repo.list_api_keys()


@router.delete("/api-keys/{key_id}", response_model=ApiKeyItemResponse)
async def revoke_virtual_api_key(
    key_id: int,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """เพิกถอน (ปิดการใช้งาน) Virtual API Key ทันที"""
    admin_repo = AdminRepository(db)
    log_repo = LogRepository(db)

    revoked_key = await admin_repo.revoke_api_key(key_id)
    if not revoked_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found.")

    await log_repo.create_audit_log(
        action="REVOKE_API_KEY",
        target_resource=f"api_key:{revoked_key.id}",
        admin_user_id=current_admin.id,
        details=f"Revoked key '{revoked_key.key_name}' ({revoked_key.key_prefix})",
        ip_address=request.client.host if request.client else None,
    )
    return revoked_key


# ==========================================
# 3. จัดการค่าย AI ปลายทาง (Providers)
# ==========================================
@router.post("/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def register_provider(
    payload: ProviderCreateRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """เพิ่มค่าย AI ปลายทาง (เข้ารหัส API Key จริงด้วย Fernet อัตโนมัติ)"""
    admin_repo = AdminRepository(db)
    log_repo = LogRepository(db)

    provider = await admin_repo.create_provider(
        name=payload.name,
        provider_type=payload.provider_type,
        base_url=payload.base_url,
        default_model=payload.default_model,
        raw_api_key=payload.api_key,
        priority=payload.priority,
    )

    await log_repo.create_audit_log(
        action="REGISTER_PROVIDER",
        target_resource=f"provider:{provider.name}",
        admin_user_id=current_admin.id,
        details=f"Registered {provider.provider_type} ({provider.base_url})",
        ip_address=request.client.host if request.client else None,
    )
    return provider


@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """ดูรายชื่อค่าย AI ปลายทางทั้งหมด"""
    admin_repo = AdminRepository(db)
    return await admin_repo.list_providers()