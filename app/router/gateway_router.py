import time
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.handlers.base_handler import BaseHandler
from app.handlers.mock_handler import MockHandler
from app.hooks.usage_logger import UsageLoggerHook
from app.repositories.models import Provider
from app.repositories.provider_repo import ProviderRepository
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse


class GatewayRouter:
    """
    ตัวกลางควบคุมเส้นทางคำขอ (Core Routing Engine)
    ทำหน้าที่เลือก Handler, วัดเวลาประมวลผล และสั่งบันทึก Usage Log ลงฐานข้อมูล
    """

    def __init__(self):
        self.mock_handler: BaseHandler = MockHandler()

    def _select_handler(self, provider: Provider) -> BaseHandler:
        if provider.provider_type == "mock":
            return self.mock_handler
        raise HTTPException(
            status_code=503,
            detail=f"Provider type is not supported: {provider.provider_type}",
        )

    async def route_chat_completion(
        self,
        request: ChatCompletionRequest,
        db: AsyncSession,
        api_key_id: Optional[int] = None,
    ) -> ChatCompletionResponse:
        """รับคำขอแชท ส่งต่อให้ Handler ประมวลผล พร้อมบันทึกประวัติลงฐานข้อมูล"""
        start_time = time.perf_counter()

        try:
            provider = await ProviderRepository.find_active_by_model(
                db=db,
                model_name=request.model,
            )
            if provider is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No active provider found for model: {request.model}",
                )

            handler = self._select_handler(provider)

            # 1. สั่งประมวลผลคำขอ
            response = await handler.chat_completion(request)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # 2. บันทึกประวัติกรณีสำเร็จ (Status 200) ลงตาราง usage_logs
            await UsageLoggerHook.log_success(
                db=db,
                response=response,
                latency_ms=latency_ms,
                api_key_id=api_key_id,
            )
            return response

        except HTTPException as exc:
            # 3. หากเกิด HTTPException ให้บันทึกประวัติความล้มเหลวไว้ด้วย
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            await UsageLoggerHook.log_failure(
                db=db,
                model_name=request.model,
                provider_name="built-in-mock",
                latency_ms=latency_ms,
                status_code=exc.status_code,
                error_message=str(exc.detail),
                api_key_id=api_key_id,
            )
            raise exc