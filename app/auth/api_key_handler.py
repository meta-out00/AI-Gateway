from fastapi import Header, HTTPException


API_KEY = "test-key"


def verify_api_key(authorization: str | None = Header(default=None)):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )

    return True