import time
import uuid
from typing import Any, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.log_repo import LogRepository
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse


class UsageLoggerHook:
    """Hook สำหรับบันทึกข้อมูล Telemetry หลังจบการเรียกใช้ AI (ทั้งกรณีสำเร็จและเกิด Error)"""

    #เพิ่ม
    @staticmethod
    async def execute_and_log(
        db: AsyncSession,
        request: ChatCompletionRequest,
        handler: Any,
        provider_name: str,
        api_key_id: Optional[int] = None,
    ) -> ChatCompletionResponse:
        start_time = time.perf_counter()
        try:
            response: ChatCompletionResponse = await handler.chat_completion(request)
            latency_ms = (time.perf_counter() - start_time) * 1000
            await UsageLoggerHook.log_success(
                db=db,
                response=response,
                latency_ms=latency_ms,
                api_key_id=api_key_id,
            )
            return response
        except HTTPException as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            await UsageLoggerHook.log_failure(
                db=db,
                model_name=request.model,
                provider_name=provider_name,
                latency_ms=latency_ms,
                status_code=exc.status_code,
                error_message=str(exc.detail),
                api_key_id=api_key_id,
            )
            raise
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            await UsageLoggerHook.log_failure(
                db=db,
                model_name=request.model,
                provider_name=provider_name,
                latency_ms=latency_ms,
                status_code=500,
                error_message=str(exc),
                api_key_id=api_key_id,
            )
            raise

    @staticmethod
    async def log_success(
        db: AsyncSession,
        response: ChatCompletionResponse,
        latency_ms: float,
        api_key_id: Optional[int] = None,
    ) -> None:
        """บันทึก Log เมื่อ AI ตอบกลับสำเร็จ (Status 200)"""
        log_repo = LogRepository(db)
        usage = response.usage
        request_id = getattr(response, "id", None) or f"req-{uuid.uuid4().hex[:12]}"
        await log_repo.create_usage_log(
            request_id=request_id,
            api_key_id=api_key_id,
            model_name=response.model,
            provider_name=response.provider or "unknown",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=round(latency_ms, 2),
            status_code=200,
            error_message=None,
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
        request_id: Optional[str] = None,
    ) -> None:
        """บันทึก Log เมื่อเกิดข้อผิดพลาดจากค่าย AI (เช่น 429, 500, 503)"""
        log_repo = LogRepository(db)
        await log_repo.create_usage_log(
            request_id=request_id or f"req-{uuid.uuid4().hex[:12]}",
            api_key_id=api_key_id,
            model_name=model_name,
            provider_name=provider_name,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=round(latency_ms, 2),
            status_code=status_code,
            error_message=error_message[:1000],
        )