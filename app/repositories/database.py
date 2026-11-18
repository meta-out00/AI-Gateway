from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# 1. สร้างเครื่องยนต์เชื่อมต่อฐานข้อมูลแบบ Async (Async Engine)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # ถ้า DEBUG=True จะพิมพ์คำสั่ง SQL ออกมาให้ดูใน Terminal
    pool_pre_ping=True,   # ตรวจสอบว่าสายเชื่อมต่อยังใช้งานได้ปกติก่อนส่งคำสั่ง SQL
)

# 2. สร้างโรงงานผลิต Session (Session Factory) สำหรับคุยกับฐานข้อมูลในแต่ละ Request
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ป้องกันไม่ให้ข้อมูลใน Object หายไปหลังจากสั่ง commit()
    autoflush=False,
)


# 3. สร้างคลาสแม่แบบ (Base Class) สำหรับนำไปสร้างตารางในไฟล์ models.py
class Base(DeclarativeBase):
    """คลาสแม่แบบสำหรับ ORM Models ทั้งหมดในระบบ"""
    pass


# 4. Dependency สำหรับแจกจ่าย Database Session ให้กับ FastAPI Endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """เปิด Session เมื่อมี Request เข้ามา และปิดให้อัตโนมัติเมื่อจบการทำงาน"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()