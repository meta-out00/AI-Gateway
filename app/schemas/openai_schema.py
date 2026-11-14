from pydantic import BaseModel


class ChatRequest(BaseModel):
    provider: str
    model: str
    message: str


class ChatResponse(BaseModel):
    provider: str
    model: str
    response: str