import json
import time
import uuid
from collections.abc import AsyncGenerator
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
    รองรับทั้งแบบรอจบประโยค (Non-Streaming) และไหลทีละคำ (SSE Streaming)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        provider_name: str = "openai-compatible",
        read_timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.provider_name = provider_name
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=read_timeout,
            write=10.0,
            pool=10.0,
        )

    def _normalize_messages(self, model_name: str, messages: list) -> list[dict]:
        """ปรับแต่งโครงสร้าง messages ให้อัตโนมัติตามข้อจำกัดของแต่ละค่าย/โมเดล"""
        normalized = [msg.model_dump() for msg in messages]

        if model_name.startswith("gemini-"):
            has_user_msg = any(m["role"] == "user" for m in normalized)
            if not has_user_msg and normalized:
                normalized[-1]["role"] = "user"

        if model_name.startswith(("o1-", "o3-")):
            for m in normalized:
                if m["role"] == "system":
                    m["role"] = "developer"

        return normalized

    def _build_payload(self, request: ChatCompletionRequest, stream: bool) -> dict:
        payload = {
            "model": request.model,
            "messages": self._normalize_messages(request.model, request.messages),
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = self._build_payload(request, stream=False)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.ConnectTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Connection to upstream AI provider timed out (10s).",
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Upstream AI provider took too long to generate a response.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to upstream AI provider: {str(exc)}",
            )

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
        choices = [
            ChatCompletionChoice(
                index=item.get("index", idx),
                message=ChatMessage(
                    role=item.get("message", {}).get("role", "assistant"),
                    content=item.get("message", {}).get("content", ""),
                ),
                finish_reason=item.get("finish_reason", "stop"),
            )
            for idx, item in enumerate(data.get("choices", []))
        ]

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

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = self._build_payload(request, stream=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=headers
                ) as response:
                    if response.status_code >= 400:
                        raw_err = await response.aread()
                        try:
                            err_json = json.loads(raw_err.decode("utf-8"))
                            err_msg = err_json.get("error", {}).get(
                                "message", raw_err.decode("utf-8")
                            )
                        except Exception:
                            err_msg = raw_err.decode("utf-8", errors="ignore")

                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Upstream Provider Error: {err_msg}",
                        )

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
        except httpx.ConnectTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Connection to upstream AI provider timed out (10s).",
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Upstream AI provider stream timed out.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to upstream AI provider: {str(exc)}",
            )