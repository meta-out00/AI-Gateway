from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.api_key_handler import verify_virtual_api_key
from app.repositories.database import get_db
from app.repositories.models import ApiKey
from app.router.gateway_router import GatewayRouter
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter(prefix="/v1", tags=["Data Plane - Chat Completions"])
gateway_router = GatewayRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: ApiKey = Depends(verify_virtual_api_key),
    x_provider_api_key: str | None = Header(
        default=None,
        alias="X-Provider-Api-Key",
        description="Optional: พก API Key ของค่าย AI ส่วนตัวมาเอง (BYOK) เพื่อใช้แทนคีย์กลางของระบบ",
    ),
    db: AsyncSession = Depends(get_db),
) -> ChatCompletionResponse:
    """
    Endpoint หลักสำหรับรับคำขอสนทนาตามมาตรฐาน OpenAI API
    - รองรับทั้ง Mock AI (mock-*) และค่าย AI จริง (OpenAI, Gemini, Ollama)
    - รองรับทั้งคีย์กลางที่แอดมินตั้งค่าไว้ และ BYOK ผ่าน Header X-Provider-Api-Key
    """
    return await gateway_router.route_chat_completion(
        request=request,
        db=db,
        api_key_id=api_key.id,
        byok_api_key=x_provider_api_key,
    )