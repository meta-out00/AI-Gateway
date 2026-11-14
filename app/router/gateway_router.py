from app.handlers.mock_openai import MockOpenAI
from app.handlers.mock_claude import MockClaude
from app.handlers.mock_gemini import MockGemini

from app.transformers import (
    openai_transformer,
    claude_transformer,
    gemini_transformer
)


class GatewayRouter:

    def __init__(self):

        self.providers = {
            "openai": {
                "models": [
                    "gpt-6-luna",
                    "gpt-6.1-sol"
                ],
                "handler": MockOpenAI(),
                "transformer": openai_transformer
            },

            "claude": {
                "models": [
                    "claude-sonnet",
                    "claude-haiku"
                ],
                "handler": MockClaude(),
                "transformer": claude_transformer
            },

            "gemini": {
                "models": [
                    "gemini-2.5-pro",
                    "gemini-2.5-flash"
                ],
                "handler": MockGemini(),
                "transformer": gemini_transformer
            }
        }

    async def route(
        self,
        provider: str,
        model: str,
        message: str
    ) -> dict:

        # 1. ตรวจสอบ Provider
        config = self.providers.get(provider)

        if config is None:
            raise ValueError(
                f"Provider '{provider}' not found"
            )

        # 2. ตรวจสอบ Model ของ Provider นั้น
        if model not in config["models"]:
            raise ValueError(
                f"Model '{model}' is not available "
                f"for provider '{provider}'"
            )

        # 3. เลือก Handler
        handler = config["handler"]

        # 4. เลือก Transformer
        transformer = config["transformer"]

        # 5. แปลง Common Request
        #    → Provider Request
        provider_request = transformer.transform_request(
            model,
            message
        )

        # 6. ส่งให้ Provider
        provider_response = await handler.generate(
            provider_request
        )

        # 7. แปลง Provider Response
        #    → Common Response
        response = transformer.transform_response(
            provider_response
        )

        return {
            "provider": provider,
            "model": model,
            "response": response
        }


gateway_router = GatewayRouter()