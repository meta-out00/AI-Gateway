import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash
from app.config import settings

password_hasher = PasswordHash.recommended()


# ==========================================
# 1. การจัดการรหัสผ่านแอดมิน (Argon2 One-Way Hash)
# ==========================================
def hash_password(plain_password: str) -> str:
    """เข้ารหัสรหัสผ่านด้วย Argon2 (ไม่สามารถถอดรหัสย้อนกลับได้)"""
    return password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ตรวจสอบรหัสผ่านที่กรอกเข้ามาว่าตรงกับค่า Hash ในฐานข้อมูลหรือไม่"""
    return password_hasher.verify(plain_password, hashed_password)


# ==========================================
# 2. การจัดการ Virtual API Key (Data Plane)
# ==========================================
def generate_virtual_api_key() -> tuple[str, str, str]:
    """
    สร้าง Virtual API Key ใหม่สำหรับแจกให้ผู้ใช้งาน
    คืนค่า 3 ส่วน: (raw_key ที่โชว์ครั้งเดียว, key_prefix, hashed_key สำหรับเก็บลง DB)
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"sk-gw-{random_part}"
    key_prefix = f"{raw_key[:12]}..."
    hashed_key = hash_api_key(raw_key)
    return raw_key, key_prefix, hashed_key


def hash_api_key(raw_key: str) -> str:
    """แปลง Virtual API Key เป็น SHA-256 เพื่อใช้ค้นหาใน PostgreSQL อย่างรวดเร็ว"""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# ==========================================
# 3. เข้ารหัส-ถอดรหัส API Key ของค่าย AI จริง (Fernet Two-Way Encryption)
# ==========================================
def _get_fernet() -> Fernet:
    return Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))


def encrypt_provider_key(raw_provider_key: str) -> str:
    """เข้ารหัส API Key จริงของค่าย AI (เช่น OpenAI/Gemini) ก่อนบันทึกลง PostgreSQL"""
    return _get_fernet().encrypt(raw_provider_key.encode("utf-8")).decode("utf-8")


def decrypt_provider_key(encrypted_key: str) -> str:
    """ถอดรหัส API Key จริงของค่าย AI เพื่อนำไปใส่ Header ตอนยิงออกเน็ต"""
    return _get_fernet().decrypt(encrypted_key.encode("utf-8")).decode("utf-8")


# ==========================================
# 4. สร้างและตรวจสอบ JWT Token ของแอดมิน (Control Plane)
# ==========================================
def create_access_token(subject: str, role: str = "admin") -> str:
    """สร้าง JWT Token สำหรับแอดมินที่ล็อกอินสำเร็จ"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict | None:
    """ตรวจสอบความถูกต้องและวันหมดอายุของ JWT Token"""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None