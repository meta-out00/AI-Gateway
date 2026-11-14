from fastapi import FastAPI

from app.endpoints.chat_endpoint import router as chat_router


app = FastAPI(
    title="AI Service Gateway",
    version="1.0.0"
)

app.include_router(chat_router)