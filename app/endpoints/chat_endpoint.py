from fastapi import APIRouter, Depends
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
    db: AsyncSession = Depends(get_db),
) -> ChatCompletionResponse:
    """
    Endpoint หลักสำหรับรับคำขอสนทนาตามมาตรฐาน OpenAI API
    - บังคับตรวจสอบ Virtual API Key (Bearer sk-gw-...)
    - บันทึก Usage Log พร้อมผูก api_key_id ลง PostgreSQL อัตโนมัติ
    """
    return await gateway_router.route_chat_completion(
        request=request,
        db=db,
        api_key_id=api_key.id,
    )