from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import (
    encrypt_provider_key,
    generate_virtual_api_key,
    hash_password,
)
from app.config import settings
from app.repositories.models import ApiKey, Provider, RolePolicy, User


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
        role_name: str | None = None,
        rate_limit_per_minute: int | None = None,
        max_budget_usd: float | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        raw_key, key_prefix, hashed_key = generate_virtual_api_key()
        new_key = ApiKey(
            key_name=key_name,
            key_prefix=key_prefix,
            hashed_key=hashed_key,
            user_id=user_id,
            role_name=role_name,
            rate_limit_per_minute=rate_limit_per_minute,
            max_budget_usd=max_budget_usd,
            current_spend_usd=0.0,
            is_active=True,
            expires_at=expires_at,
        )
        self.db.add(new_key)
        await self.db.commit()
        await self.db.refresh(new_key)
        return new_key, raw_key

    async def seed_default_roles(self) -> None:
        """สร้างกลุ่มสิทธิ์มาตรฐานเริ่มต้นอัตโนมัติ หากยังไม่มีในฐานข้อมูล"""
        default_roles = [
            {
                "role_name": "admin",
                "description": "ผู้ดูแลระบบ (ไม่จำกัดงบและใช้ได้ทุกรุ่น)",
                "default_rate_limit_per_minute": 1000,
                "default_max_budget_usd": None,
                "allowed_models": "*",
            },
            {
                "role_name": "student",
                "description": "นักศึกษา (งบ $2, 20 RPM, โมเดลรุ่นประหยัด)",
                "default_rate_limit_per_minute": 20,
                "default_max_budget_usd": 2.0,
                "allowed_models": "mock-,gemini-flash-lite,gpt-4o-mini",
            },
            {
                "role_name": "lecturer",
                "description": "อาจารย์ (งบ $20, 60 RPM, ใช้ได้ทุกรุ่น)",
                "default_rate_limit_per_minute": 60,
                "default_max_budget_usd": 20.0,
                "allowed_models": "*",
            },
            {
                "role_name": "expert",
                "description": "ผู้เชี่ยวชาญ (งบ $50, 120 RPM, ใช้ได้ทุกรุ่น)",
                "default_rate_limit_per_minute": 120,
                "default_max_budget_usd": 50.0,
                "allowed_models": "*",
            },
        ]

        created_any = False
        for item in default_roles:
            existing = await self.get_role_by_name(item["role_name"])
            if not existing:
                self.db.add(RolePolicy(**item))
                created_any = True

        if created_any:
            await self.db.commit()
            print("[Seed] Initialized default role policies (admin, student, lecturer, expert).")

    async def list_roles(self) -> list[RolePolicy]:
        result = await self.db.execute(select(RolePolicy).order_by(RolePolicy.id.asc()))
        return list(result.scalars().all())

    async def get_role_by_id(self, role_id: int) -> RolePolicy | None:
        result = await self.db.execute(select(RolePolicy).where(RolePolicy.id == role_id))
        return result.scalar_one_or_none()

    async def get_role_by_name(self, role_name: str) -> RolePolicy | None:
        result = await self.db.execute(
            select(RolePolicy).where(RolePolicy.role_name == role_name.strip().lower())
        )
        return result.scalar_one_or_none()

    async def create_role(
        self,
        role_name: str,
        description: str | None,
        default_rate_limit_per_minute: int,
        default_max_budget_usd: float | None,
        allowed_models: str,
    ) -> RolePolicy:
        role = RolePolicy(
            role_name=role_name.strip().lower(),
            description=description,
            default_rate_limit_per_minute=default_rate_limit_per_minute,
            default_max_budget_usd=default_max_budget_usd,
            allowed_models=allowed_models.strip() or "*",
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update_role(
        self,
        role: RolePolicy,
        updates: dict,
    ) -> RolePolicy:
        for field, value in updates.items():
            setattr(role, field, value)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def count_api_keys_by_role(self, role_name: str) -> int:
        result = await self.db.execute(
            select(func.count(ApiKey.id)).where(ApiKey.role_name == role_name)
        )
        return result.scalar_one()

    async def delete_role(self, role: RolePolicy) -> None:
        await self.db.delete(role)
        await self.db.commit()

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