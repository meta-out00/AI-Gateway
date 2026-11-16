from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application Settings ---
    APP_NAME: str = "AI Gateway System"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str

    # --- Security & JWT (สำหรับ Admin Control Plane) ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Encryption Key (สำหรับเข้ารหัส API Key ของค่าย AI ด้วย Fernet) ---
    ENCRYPTION_KEY: str

    # --- Default Admin (บัญชีแอดมินเริ่มต้น) ---
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin1234"

    # ตั้งค่าให้อ่านจากไฟล์ .env ที่อยู่ระดับนอกสุด
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # ข้ามตัวแปรอื่นๆ ใน .env ที่ไม่ได้ประกาศไว้ในคลาสนี้
    )


@lru_cache
def get_settings() -> Settings:
    """สร้างและแคชออบเจกต์ Settings ไว้ในหน่วยความจำ ไม่ต้องอ่านไฟล์ .env ซ้ำทุกครั้ง"""
    return Settings()


# สร้างตัวแปรกลางเพื่อให้ไฟล์อื่น import ไปใช้ได้ทันที
settings = get_settings()