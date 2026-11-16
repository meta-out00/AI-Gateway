import asyncio
from fastapi import HTTPException
from app.handlers.base_handler import BaseHandler
from app.schemas.openai_schema import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


class MockHandler(BaseHandler):
    """ตัวจำลองผู้ให้บริการ AI (Mock AI Simulator) สำหรับทดสอบระบบโดยไม่เสียค่าใช้จ่าย"""

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        # 1. จำลองความหน่วงของเครือข่าย (Latency Simulation)
        if request.mock_delay and request.mock_delay > 0:
            await asyncio.sleep(request.mock_delay)

        # 2. จำลองข้อผิดพลาดจากค่าย AI (Fault Injection)
        if request.mock_error_code:
            raise HTTPException(
                status_code=request.mock_error_code,
                detail=f"Simulated error {request.mock_error_code} from Mock AI Provider",
            )

        # 3. ดึงข้อความล่าสุดที่ผู้ใช้พิมพ์เข้ามา
        last_user_message = request.messages[-1].content
        reply_text = f"[Mock AI - {request.model}] ได้รับข้อความของคุณแล้ว: '{last_user_message}'"

        # 4. คำนวณจำนวน Token แบบจำลอง
        prompt_tokens = len(last_user_message.split())
        completion_tokens = len(reply_text.split())

        # 5. ประกอบร่างคำตอบตามมาตรฐาน OpenAI Schema
        return ChatCompletionResponse(
            model=request.model,
            provider="built-in-mock",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=reply_text),
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )