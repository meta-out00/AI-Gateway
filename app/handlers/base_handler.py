from abc import ABC, abstractmethod
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse


class BaseHandler(ABC):
    """
    Abstract Base Class (Interface) บังคับมาตรฐานสำหรับ AI Provider ทุกค่าย
    เพื่อให้ GatewayRouter สามารถเรียกใช้งานทุกค่ายด้วยคำสั่งเดียวกัน
    """

    @abstractmethod
    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """รับ ChatCompletionRequest และต้องคืนค่าเป็น ChatCompletionResponse เสมอ"""
        pass