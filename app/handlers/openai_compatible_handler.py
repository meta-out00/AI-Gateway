import time
import uuid
import httpx
from fastapi import HTTPException, status
from app.handlers.base_handler import BaseHandler
from app.schemas.openai_schema import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


class OpenAICompatibleHandler(BaseHandler):
    """
    ตัวเชื่อมต่อค่าย AI ภายนอกที่ใช้มาตรฐาน OpenAI-Compatible API
    รองรับ OpenAI, Google Gemini (OpenAI endpoint), OpenRouter, Groq และ Ollama
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        provider_name: str = "openai-compatible",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.provider_name = provider_name
        self.timeout = timeout

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        url = f"{self.base_url}/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # เตรียม Payload ตามมาตรฐาน OpenAI (ตัดฟิลด์จำลอง mock_* ออกก่อนส่งออกเน็ต)
        payload = {
            "model": request.model,
            "messages": [msg.model_dump() for msg in request.messages],
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Upstream AI provider timed out after {self.timeout}s.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to upstream AI provider: {str(exc)}",
            )

        # จัดการกรณีค่ายปลายทางตอบกลับมาเป็น Error (เช่น 401 Invalid Key, 429 Quota Exceeded)
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text

            raise HTTPException(
                status_code=response.status_code,
                detail=f"Upstream Provider Error: {error_msg}",
            )

        data = response.json()

        # แปลงผลลัพธ์จากค่ายปลายทางให้ตรงกับ ChatCompletionResponse ของ Gateway
        choices = []
        for idx, item in enumerate(data.get("choices", [])):
            msg_data = item.get("message", {})
            choices.append(
                ChatCompletionChoice(
                    index=item.get("index", idx),
                    message=ChatMessage(
                        role=msg_data.get("role", "assistant"),
                        content=msg_data.get("content", ""),
                    ),
                    finish_reason=item.get("finish_reason", "stop"),
                )
            )

        usage_data = data.get("usage", {})
        usage = CompletionUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return ChatCompletionResponse(
            id=data.get("id", f"chatcmpl-{uuid.uuid4().hex[:12]}"),
            object=data.get("object", "chat.completion"),
            created=data.get("created", int(time.time())),
            model=data.get("model", request.model),
            provider=self.provider_name,
            choices=choices,
            usage=usage,
        )