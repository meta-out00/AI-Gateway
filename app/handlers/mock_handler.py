import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator
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
    """ตัวจำลองผู้ให้บริการ AI (Mock AI Simulator) สำหรับทดสอบระบบทั้งแบบปกติและ Streaming"""

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        if request.mock_delay and request.mock_delay > 0:
            await asyncio.sleep(request.mock_delay)

        if request.mock_error_code:
            raise HTTPException(
                status_code=request.mock_error_code,
                detail=f"Simulated error {request.mock_error_code} from Mock AI Provider",
            )

        last_user_message = request.messages[-1].content
        reply_text = f"[Mock AI - {request.model}] ได้รับข้อความของคุณแล้ว: '{last_user_message}'"

        prompt_tokens = len(last_user_message.split())
        completion_tokens = len(reply_text.split())

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

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[str, None]:
        if request.mock_delay and request.mock_delay > 0:
            await asyncio.sleep(request.mock_delay)

        if request.mock_error_code:
            raise HTTPException(
                status_code=request.mock_error_code,
                detail=f"Simulated error {request.mock_error_code} from Mock AI Provider",
            )

        last_user_message = request.messages[-1].content
        reply_text = f"[Mock Stream - {request.model}] กำลังส่งคำตอบทีละส่วนสำหรับ: '{last_user_message}'"
        words = reply_text.split(" ")

        stream_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_ts = int(time.time())

        # Chunk แรกส่ง role: assistant ตามมาตรฐาน OpenAI SSE
        first_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"

        # ทยอยส่งเนื้อหาทีละคำ
        for idx, word in enumerate(words):
            token_text = word if idx == 0 else f" {word}"
            chunk = {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token_text},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)

        # Chunk ปิดท้ายพร้อมยอด Usage
        prompt_tokens = len(last_user_message.split())
        completion_tokens = len(words)
        final_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": request.model,
            "choices": [],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"