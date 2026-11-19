from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import decrypt_provider_key
from app.handlers.mock_handler import MockHandler
from app.handlers.openai_compatible_handler import OpenAICompatibleHandler
from app.hooks.usage_logger import UsageLoggerHook
from app.repositories.admin_repo import AdminRepository
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse


class GatewayRouter:
    """
    ตัวกลางควบคุมเส้นทางคำขอ (Routing Engine)
    - แยกคำขอระหว่าง Mock Simulator และ Real AI Providers
    - รองรับทั้ง Managed Key (จาก DB) และ BYOK (X-Provider-Api-Key)
    """

    def __init__(self):
        self.mock_handler = MockHandler()
        self.usage_logger = UsageLoggerHook()

    def _infer_default_base_url(self, model_name: str) -> str:
        """กำหนด Base URL เริ่มต้นกรณีผู้ใช้ส่ง BYOK Key มาโดยยังไม่ได้ลงทะเบียน Provider ใน DB"""
        if model_name.startswith("gemini-"):
            return "https://generativelanguage.googleapis.com/v1beta/openai"
        return "https://api.openai.com/v1"

    async def route_chat_completion(
        self,
        request: ChatCompletionRequest,
        db: AsyncSession,
        api_key_id: int | None = None,
        byok_api_key: str | None = None,
    ) -> ChatCompletionResponse:
        # 1. กรณีเรียกใช้งาน Mock Simulator
        if request.model.startswith("mock-"):
            return await self.usage_logger.execute_and_log(
                db=db,
                request=request,
                handler=self.mock_handler,
                provider_name="mock-provider",
                api_key_id=api_key_id,
            )

        # 2. กรณีเรียกใช้งานค่าย AI จริง (Real Provider)
        admin_repo = AdminRepository(db)
        provider = await admin_repo.get_active_provider_for_model(request.model)

        # ถ้า Provider ที่เจอใน DB เป็นประเภท mock ให้เข้า MockHandler ทันที ไม่ออกเน็ตไป base_url
        if provider and provider.provider_type == "mock":
            return await self.usage_logger.execute_and_log(
                db=db,
                request=request,
                handler=self.mock_handler,
                provider_name=provider.name,
                api_key_id=api_key_id,
            )

        if provider:
            base_url = provider.base_url
            provider_name = provider.name
            # ลำดับความสำคัญ: ใช้คีย์ส่วนตัว (BYOK) ก่อน ถ้าไม่มีค่อยถอดรหัสคีย์กลางจาก DB
            if byok_api_key:
                resolved_api_key = byok_api_key
            elif provider.encrypted_api_key:
                resolved_api_key = decrypt_provider_key(provider.encrypted_api_key)
            else:
                resolved_api_key = None
        else:
            # กรณีแอดมินยังไม่ได้ลงทะเบียน Provider ใน DB แต่ผู้ใช้พกคีย์ส่วนตัว (BYOK) มาเอง
            if not byok_api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"No active AI provider configured for model '{request.model}'. "
                        "Either register a provider via /admin/providers or pass your own key via 'X-Provider-Api-Key' header."
                    ),
                )
            base_url = self._infer_default_base_url(request.model)
            provider_name = "byok-direct"
            resolved_api_key = byok_api_key

        real_handler = OpenAICompatibleHandler(
            base_url=base_url,
            api_key=resolved_api_key,
            provider_name=provider_name,
        )

        return await self.usage_logger.execute_and_log(
            db=db,
            request=request,
            handler=real_handler,
            provider_name=provider_name,
            api_key_id=api_key_id,
        )