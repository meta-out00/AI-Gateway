from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import (
    encrypt_provider_key,
    generate_virtual_api_key,
    hash_password,
)
from app.config import settings
from app.repositories.models import ApiKey, Provider, User


class AdminRepository:
    """จัดการคำสั่งฐานข้อมูลสำหรับ Control Plane (Users, API Keys, Providers)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- 1. จัดการผู้ใช้งาน (Users) ---
    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def seed_default_admin(self) -> User:
        """สร้างบัญชีแอดมินเริ่มต้นอัตโนมัติ หากยังไม่มีในฐานข้อมูล"""
        existing_admin = await self.get_user_by_username(settings.DEFAULT_ADMIN_USERNAME)
        if existing_admin:
            return existing_admin

        new_admin = User(
            username=settings.DEFAULT_ADMIN_USERNAME,
            hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        self.db.add(new_admin)
        await self.db.commit()
        await self.db.refresh(new_admin)
        print(f"[Seed] Created default admin user: '{new_admin.username}'")
        return new_admin

    # --- 2. จัดการ Virtual API Keys ---
    async def create_api_key(
        self,
        key_name: str,
        user_id: int,
        rate_limit_per_minute: int = 60,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """สร้าง Virtual API Key ใหม่ คืนค่า (ApiKey Record, raw_key ที่โชว์ครั้งเดียว)"""
        raw_key, key_prefix, hashed_key = generate_virtual_api_key()
        new_key = ApiKey(
            key_name=key_name,
            key_prefix=key_prefix,
            hashed_key=hashed_key,
            user_id=user_id,
            rate_limit_per_minute=rate_limit_per_minute,
            is_active=True,
            expires_at=expires_at,
        )
        self.db.add(new_key)
        await self.db.commit()
        await self.db.refresh(new_key)
        return new_key, raw_key

    async def list_api_keys(self) -> list[ApiKey]:
        result = await self.db.execute(select(ApiKey).order_by(ApiKey.id.desc()))
        return list(result.scalars().all())

    async def revoke_api_key(self, key_id: int) -> ApiKey | None:
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == key_id))
        api_key = result.scalar_one_or_none()
        if not api_key:
            return None
        api_key.is_active = False
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    # --- 3. จัดการค่าย AI ปลายทาง (Providers) ---
    async def create_provider(
        self,
        name: str,
        provider_type: str,
        base_url: str,
        default_model: str,
        raw_api_key: str | None = None,
        priority: int = 1,
    ) -> Provider:
        """เพิ่มค่าย AI ปลายทาง พร้อมเข้ารหัส API Key จริงด้วย Fernet ก่อนบันทึก"""
        encrypted_key = encrypt_provider_key(raw_api_key) if raw_api_key else None
        provider = Provider(
            name=name,
            provider_type=provider_type,
            base_url=base_url,
            encrypted_api_key=encrypted_key,
            default_model=default_model,
            priority=priority,
            is_active=True,
        )
        self.db.add(provider)
        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def list_providers(self) -> list[Provider]:
        result = await self.db.execute(
            select(Provider).order_by(Provider.priority.asc(), Provider.id.asc())
        )
        return list(result.scalars().all())

    async def get_active_provider_for_model(self, model_name: str) -> Provider | None:
        """
        ค้นหา Provider ที่เปิดใช้งานอยู่โดยเรียงตาม priority (เลขน้อย = สำคัญกว่า)
        - หากมี Provider ที่ตั้ง default_model ตรงกับ model_name จะเลือกตัวนั้นก่อน
        - หากไม่มี จะดึง Provider หลักที่มี priority สูงสุดมาใช้งาน
        """
        providers = await self.list_providers()
        active_providers = [p for p in providers if p.is_active]
        if not active_providers:
            return None

        for provider in active_providers:
            if provider.default_model == model_name:
                return provider

        return active_providers[0]