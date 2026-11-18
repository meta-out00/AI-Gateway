from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import Provider


class ProviderRepository:
    """ค้นหา Provider ที่เปิดใช้งานจากฐานข้อมูล"""

    DEFAULT_PROVIDERS = (
        {
            "name": "local-mock",
            "provider_type": "mock",
            "base_url": "http://localhost",
            "default_model": "mock-gpt-4o",
            "priority": 1,
        },
        {
            "name": "local-claude-mock",
            "provider_type": "mock",
            "base_url": "http://localhost",
            "default_model": "claude-3-5-sonnet",
            "priority": 1,
        },
        {
            "name": "local-gemini-mock",
            "provider_type": "mock",
            "base_url": "http://localhost",
            "default_model": "gemini-2.0-flash",
            "priority": 1,
        },
    )

    @staticmethod
    async def find_active_by_model(
        db: AsyncSession,
        model_name: str,
    ) -> Optional[Provider]:
        result = await db.execute(
            select(Provider)
            .where(
                Provider.default_model == model_name,
                Provider.is_active.is_(True),
            )
            .order_by(Provider.priority.asc())
        )
        return result.scalars().first()

    @staticmethod
    async def ensure_default_providers(db: AsyncSession) -> None:
        result = await db.execute(select(Provider.name))
        existing_names = set(result.scalars().all())

        for provider_data in ProviderRepository.DEFAULT_PROVIDERS:
            if provider_data["name"] not in existing_names:
                db.add(Provider(**provider_data, is_active=True))

        await db.commit()
