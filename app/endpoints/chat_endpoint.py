from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.database import get_db
from app.router.gateway_router import GatewayRouter
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter(prefix="/v1", tags=["Data Plane - Chat Completions"])
gateway_router = GatewayRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatCompletionResponse:
    """
    Endpoint หลักสำหรับรับคำขอสนทนาตามมาตรฐาน OpenAI API
    พร้อมเชื่อมต่อฐานข้อมูลเพื่อบันทึก Usage Log อัตโนมัติ
    """
    return await gateway_router.route_chat_completion(request=request, db=db)