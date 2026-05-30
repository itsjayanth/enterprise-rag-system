from fastapi import APIRouter

from . import documents

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

