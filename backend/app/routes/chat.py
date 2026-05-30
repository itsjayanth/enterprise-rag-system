from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.chat import ChatHistoryResponse, ChatQueryRequest, ChatSessionResponse, MessageResponse
from ..services.chat_service import ChatService

router = APIRouter()
logger = structlog.get_logger("app.routes.chat")


@router.post("/query")
async def chat_query(payload: ChatQueryRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    service = ChatService(db)
    generator = service.stream_answer(
        query=payload.query,
        session_id=payload.session_id,
        document_ids=payload.document_ids,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db)) -> list[ChatSessionResponse]:
    service = ChatService(db)
    sessions = service.list_sessions()
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
def get_session_messages(session_id: uuid.UUID, db: Session = Depends(get_db)) -> ChatHistoryResponse:
    from ..models.chat import ChatSession

    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    service = ChatService(db)
    messages = service.get_session_messages(session_id)

    return ChatHistoryResponse(
        session=ChatSessionResponse.model_validate(session),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )

