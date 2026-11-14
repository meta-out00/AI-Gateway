from app.handlers.base_handler import AIHandler


class MockClaude(AIHandler):

    async def generate(self, request: dict) -> dict:

        print("Claude received:")
        print(request)

        return {
            "content": [
                {
                    "text": "นี่คือคำตอบจาก Mock Claude"
                }
            ]
        }