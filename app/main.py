from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.endpoints import chat_endpoint
from app.repositories.database import AsyncSessionLocal, Base, engine
from app.repositories.provider_repo import ProviderRepository
import app.repositories.models  # นำเข้าเพื่อให้ Base รู้จักตารางทั้งหมด


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ทำงานอัตโนมัติตอนเริ่มเปิดเซิร์ฟเวอร์ และตอนปิดเซิร์ฟเวอร์"""
    # 1. ตอนเริ่มเปิดเซิร์ฟเวอร์: สร้างตารางทั้งหมดใน PostgreSQL (ถ้ายังไม่มี)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await ProviderRepository.ensure_default_providers(db)

    print("[Database] Verified and initialized all PostgreSQL tables.")
    
    yield  # จุดนี้คือช่วงที่เซิร์ฟเวอร์กำลังรันรับ Request ปกติ
    
    # 2. ตอนปิดเซิร์ฟเวอร์: ปิดท่อเชื่อมต่อฐานข้อมูลทั้งหมดอย่างปลอดภัย
    await engine.dispose()
    print("[Database] Disconnected from PostgreSQL.")


# สร้างออบเจกต์หลักของแอปพลิเคชัน FastAPI พร้อมผูก lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="Modular AI Gateway รองรับมาตรฐาน OpenAI API, Mock AI Simulator และระบบจัดการสิทธิ์",
    version="1.0.0",
    lifespan=lifespan,
)

# นำเส้นทาง /v1/chat/completions มาเสียบเข้ากับแอปหลัก
app.include_router(chat_endpoint.router)


@app.get("/health", tags=["System"])
async def health_check():
    """ตรวจสอบสถานะความพร้อมของเซิร์ฟเวอร์ (ใช้สำหรับ Docker Healthcheck)"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }