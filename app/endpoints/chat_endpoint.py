from fastapi import APIRouter, HTTPException

from app.schemas.openai_schema import (
    ChatRequest,
    ChatResponse
)

from app.router.gateway_router import gateway_router


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    try:

        result = await gateway_router.route(
            provider=request.provider,
            model=request.model,
            message=request.message
        )

        return ChatResponse(**result)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )