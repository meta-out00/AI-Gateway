from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.rate_limiter import enforce_rate_limit, verify_model_access
from app.repositories.database import get_db
from app.repositories.models import ApiKey
from app.router.gateway_router import GatewayRouter
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter(prefix="/v1", tags=["Data Plane - Chat Completions"])
gateway_router = GatewayRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: ApiKey = Depends(enforce_rate_limit),
    x_provider_api_key: str | None = Header(
        default=None,
        alias="X-Provider-Api-Key",
        description="Optional: พก API Key ของค่าย AI ส่วนตัวมาเอง (BYOK) เพื่อใช้แทนคีย์กลางของระบบ",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint หลักสำหรับรับคำขอสนทนาตามมาตรฐาน OpenAI API
    - ตรวจสอบสิทธิ์ Virtual API Key, โควต้าตาม Role (งบประมาณ/ความเร็ว) และสิทธิ์เรียกใช้งานโมเดล
    - รองรับทั้งการตอบกลับแบบก้อนเดียว (stream: false) และไหลทีละคำ (stream: true)
    """
    # ตรวจสิทธิ์การเรียกใช้โมเดลตาม Role Policy (บล็อกทั้งแบบปกติและ Streaming)
    verify_model_access(api_key=api_key, model_name=request.model)

    if request.stream:
        # Resolve Handler ก่อนเริ่มสตรีม เพื่อให้คืน HTTP 400 ได้ทันทีหากตั้งค่าไม่ครบ
        handler, provider_name = await gateway_router.resolve_handler(
            request=request,
            db=db,
            byok_api_key=x_provider_api_key,
        )
        return StreamingResponse(
            gateway_router.stream_with_logging(
                handler=handler,
                provider_name=provider_name,
                request=request,
                api_key_id=api_key.id,
                is_byok=bool(x_provider_api_key and x_provider_api_key.strip()),
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await gateway_router.route_chat_completion(
        request=request,
        db=db,
        api_key_id=api_key.id,
        byok_api_key=x_provider_api_key,
    )