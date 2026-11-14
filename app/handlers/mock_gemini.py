from app.handlers.base_handler import AIHandler


class MockGemini(AIHandler):

    async def generate(self, request: dict) -> dict:

        print("Gemini received:")
        print(request)

        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "นี่คือคำตอบจาก Mock Gemini"
                            }
                        ]
                    }
                }
            ]
        }