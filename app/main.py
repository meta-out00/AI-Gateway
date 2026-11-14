from fastapi import FastAPI
from app.config import settings
from app.endpoints import chat_endpoint

# สร้างออบเจกต์หลักของแอปพลิเคชัน FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Modular AI Gateway รองรับมาตรฐาน OpenAI API, Mock AI Simulator และระบบจัดการสิทธิ์",
    version="1.0.0",
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