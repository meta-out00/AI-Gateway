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
    key_name: str = Field(..., min_length=1, max_length=100, examples=["Student Key 01"])
    role_name: str | None = Field(default="student", examples=["student"])
    rate_limit_per_minute: int | None = Field(
        default=None, ge=1, le=10000, examples=[None],
        description="ใส่ null เพื่อใช้ค่าเริ่มต้นตาม Role หรือใส่ตัวเลขเพื่อ Override เฉพาะคีย์นี้",
    )
    max_budget_usd: float | None = Field(
        default=None, ge=0, examples=[None],
        description="ใส่ null เพื่อใช้ค่าเริ่มต้นตาม Role หรือใส่ตัวเลขเพื่อ Override เฉพาะคีย์นี้",
    )
    expires_at: datetime | None = None


class ApiKeyCreateResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    raw_api_key: str
    role_name: str | None = None
    rate_limit_per_minute: int | None = None
    max_budget_usd: float | None = None
    current_spend_usd: float = 0.0
    is_active: bool
    created_at: datetime


class ApiKeyItemResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    role_name: str | None = None
    rate_limit_per_minute: int | None = None
    max_budget_usd: float | None = None
    current_spend_usd: float = 0.0
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

# --- 4. Role Policies  ---
class RolePolicyCreateRequest(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=50, examples=["researcher"])
    description: str | None = Field(default=None, max_length=255, examples=["กลุ่มนักวิจัย"])
    default_rate_limit_per_minute: int = Field(default=60, ge=1, le=10000, examples=[60])
    default_max_budget_usd: float | None = Field(default=None, ge=0, examples=[15.0])
    allowed_models: str = Field(
        default="*",
        examples=["mock-,gemini-flash-lite,gpt-4o-mini"],
        description="ใส่ '*' เพื่ออนุญาตทุกรุ่น หรือระบุ Prefix คั่นด้วยเครื่องหมายจุลภาค (,)",
    )


class RolePolicyUpdateRequest(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    default_rate_limit_per_minute: int | None = Field(default=None, ge=1, le=10000)
    default_max_budget_usd: float | None = Field(default=None, ge=0)
    allowed_models: str | None = None


class RolePolicyResponse(BaseModel):
    id: int
    role_name: str
    description: str | None
    default_rate_limit_per_minute: int
    default_max_budget_usd: float | None
    allowed_models: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- 5. Request and Audit Logs ---
class UsageLogResponse(BaseModel):
    id: int
    request_id: str
    api_key_id: int | None
    provider_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    status_code: int
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    action: str
    target_resource: str
    admin_user_id: int | None
    details: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageLogSummaryResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost_usd: float
    average_latency_ms: float