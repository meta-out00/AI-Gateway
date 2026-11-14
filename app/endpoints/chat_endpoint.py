from fastapi import APIRouter
from app.router.gateway_router import GatewayRouter
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse

# สร้างกลุ่มเส้นทาง (Sub-router) สำหรับหมวด Chat
router = APIRouter(prefix="/v1", tags=["Data Plane - Chat Completions"])

# สร้างตัวจัดการเส้นทางเตรียมไว้ใช้งาน
gateway_router = GatewayRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    Endpoint หลักสำหรับรับคำขอสนทนาตามมาตรฐาน OpenAI API
    - รับ JSON Payload ตามโครงสร้าง ChatCompletionRequest
    - ส่งต่อให้ GatewayRouter ตัดสินใจเลือก Provider และประมวลผล
    """
    return await gateway_router.route_chat_completion(request)