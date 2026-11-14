from .base_handler import AIHandler


class MockOpenAI(AIHandler):

    async def generate(self, message: str):

        return {
            "provider": "mock-openai",
            "model": "mock-model",
            "response": f"Mock OpenAI: {message}"
        }