from fastapi import APIRouter

from . import chat, documents, retrieval

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
