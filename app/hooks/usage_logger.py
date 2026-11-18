import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.log_repo import LogRepository
from app.schemas.openai_schema import ChatCompletionResponse


class UsageLoggerHook:
    """Hook สำหรับบันทึกข้อมูล Telemetry หลังจบการเรียกใช้ AI (ทั้งกรณีสำเร็จและเกิด Error)"""

    @staticmethod
    async def log_success(
        db: AsyncSession,
        response: ChatCompletionResponse,
        latency_ms: float,
        api_key_id: Optional[int] = None,
    ) -> None:
        """บันทึก Log เมื่อ AI ตอบกลับสำเร็จ (Status 200)"""
        repo = LogRepository(db)
        await repo.create_usage_log(
            request_id=response.id,
            api_key_id=api_key_id,
            provider_name=response.provider,
            model_name=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            latency_ms=latency_ms,
            status_code=200,
        )

    @staticmethod
    async def log_failure(
        db: AsyncSession,
        model_name: str,
        provider_name: str,
        latency_ms: float,
        status_code: int,
        error_message: str,
        api_key_id: Optional[int] = None,
    ) -> None:
        """บันทึก Log เมื่อเกิดข้อผิดพลาดจากค่าย AI (เช่น 429, 500, 503)"""
        repo = LogRepository(db)
        request_id = f"chatcmpl-err-{uuid.uuid4().hex[:8]}"
        await repo.create_usage_log(
            request_id=request_id,
            api_key_id=api_key_id,
            provider_name=provider_name,
            model_name=model_name,
            latency_ms=latency_ms,
            status_code=status_code,
            error_message=error_message,
        )