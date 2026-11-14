def transform_request(model: str, message: str) -> dict:
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }


def transform_response(data: dict) -> str:
    return data["choices"][0]["message"]["content"]