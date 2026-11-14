def transform_request(model: str, message: str) -> dict:
    return {
        "model": model,
        "contents": [
            {
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
        ]
    }


def transform_response(data: dict) -> str:
    return data["candidates"][0]["content"]["parts"][0]["text"]