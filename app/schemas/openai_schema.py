import time
import uuid
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="บทบาทของผู้ส่งข้อความ"
    )
    content: str = Field(..., description="เนื้อหาข้อความที่สนทนา")


class ChatCompletionRequest(BaseModel):
    model: str = Field(
        ...,
        examples=["mock-gpt-4o", "gpt-4o-mini"],
        description="ชื่อโมเดล AI ที่ต้องการเรียกใช้งาน",
    )
    messages: List[ChatMessage] = Field(
        ..., min_length=1, description="รายการข้อความบทสนทนา"
    )
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    stream: Optional[bool] = Field(
        default=False, description="เปิด/ปิดการส่งข้อมูลทีละส่วนแบบ Server-Sent Events (SSE)"
    )

    # --- พารามิเตอร์เสริมสำหรับระบบ Mock AI Simulator ---
    mock_delay: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=60.0,
        description="หน่วงเวลาจำลองเป็นวินาที (เช่น 2.5 วินาที)",
    )
    mock_error_code: Optional[int] = Field(
        default=None,
        description="จำลอง HTTP Error Code จากค่าย AI (เช่น 429 Too Many Requests, 500, 503)",
    )


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class CompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    provider: str = Field(..., description="ชื่อผู้ให้บริการ AI ที่ประมวลผลคำขอนี้")
    choices: List[ChatCompletionChoice]
    usage: CompletionUsage = Field(default_factory=CompletionUsage)