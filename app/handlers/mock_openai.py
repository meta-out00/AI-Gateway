from app.handlers.base_handler import AIHandler


class MockOpenAI(AIHandler):

    async def generate(self, request: dict) -> dict:

        print("OpenAI received:")
        print(request)

        return {
            "choices": [
                {
                    "message": {
                        "content": "นี่คือคำตอบจาก Mock OpenAI"
                    }
                }
            ]
        }