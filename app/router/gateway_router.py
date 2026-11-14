import time
from app.handlers.base_handler import BaseHandler
from app.handlers.mock_handler import MockHandler
from app.schemas.openai_schema import ChatCompletionRequest, ChatCompletionResponse


class GatewayRouter:
    """
    ตัวกลางควบคุมเส้นทางคำขอ (Core Routing Engine)
    ทำหน้าที่เลือก Handler ที่เหมาะสมตามชื่อโมเดล และวัดเวลาประมวลผล
    """

    def __init__(self):
        # เตรียมตัวจำลอง MockHandler ไว้เป็นค่าเริ่มต้นของระบบ
        self.mock_handler: BaseHandler = MockHandler()

    def _select_handler(self, model_name: str) -> BaseHandler:
        """ตัดสินใจเลือก Handler จากชื่อโมเดล (ในระยะที่ 1 ส่งเข้า MockHandler ทั้งหมด)"""
        # หมายเหตุ: ในระยะถัดไป เมื่อต่อ PostgreSQL แล้ว ส่วนนี้จะไปค้นหา Provider จริงจากฐานข้อมูล
        if model_name.startswith("mock"):
            return self.mock_handler
        return self.mock_handler

    async def route_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """รับคำขอแชท ส่งต่อให้ Handler ประมวลผล และจับเวลาการทำงาน"""
        start_time = time.perf_counter()

        # 1. เลือกตัวประมวลผลที่เหมาะสม
        handler = self._select_handler(request.model)

        # 2. สั่งประมวลผลคำขอ (ใช้คำสั่งมาตรฐานเดียวกันตามกฎของ BaseHandler)
        response = await handler.chat_completion(request)

        # 3. คำนวณเวลาที่ใช้ไปทั้งหมด (Latency) หน่วยเป็นมิลลิวินาที (ms)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        print(f"[GatewayRouter] Model: {request.model} | Provider: {response.provider} | Latency: {latency_ms} ms")

        return response