from datetime import datetime
from pydantic import BaseModel, Field


# --- 1. Authentication (Login & JWT Token) ---
class AdminLoginRequest(BaseModel):
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["admin1234"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- 2. Virtual API Keys ---
class ApiKeyCreateRequest(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=100, examples=["Mobile App Key"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    expires_at: datetime | None = None


class ApiKeyCreateResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    raw_api_key: str  # แสดงคีย์เต็มเพียงครั้งเดียวตอนสร้างเท่านั้น
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime


class ApiKeyItemResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    rate_limit_per_minute: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- 3. AI Providers ---
class ProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["openai-primary"])
    provider_type: str = Field(default="openai_compatible", examples=["openai_compatible"])
    base_url: str = Field(..., examples=["https://api.openai.com/v1"])
    api_key: str | None = Field(default=None, examples=["sk-..."])
    default_model: str = Field(..., examples=["gpt-4o-mini"])
    priority: int = Field(default=1, ge=1)


class ProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    base_url: str
    default_model: str
    priority: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}