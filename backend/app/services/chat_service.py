from __future__ import annotations

import uuid
from typing import Any, AsyncGenerator

import structlog
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from ..config import settings
from ..models.chat import ChatSession, Message
from ..services.retrieval_service import RetrievalService
from ..utils.streaming import done_event, error_event, sources_event, status_event, token_event

logger = structlog.get_logger("app.services.chat")

_SYSTEM_PROMPT = """\
You are a precise, factual assistant. Answer the user's question using ONLY the provided context.
If the answer is not present in the context, say: "I could not find the answer in the provided documents."
Always cite sources by referencing the [Source N] labels from the context.
Be concise and avoid speculation."""

_HISTORY_TURNS = 3  # number of prior user/assistant pairs to include


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm_client = AsyncOpenAI(
            base_url=settings.llm_service_url.rstrip("/"),
            api_key="ollama",
        )

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def get_or_create_session(self, session_id: str | None) -> ChatSession:
        if session_id:
            try:
                parsed_id = uuid.UUID(session_id)
                existing = self.db.get(ChatSession, parsed_id)
                if existing:
                    return existing
            except ValueError:
                pass  # invalid uuid → create new

        session = ChatSession()
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info("chat_session_created", session_id=str(session.id))
        return session

    def store_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> Message:
        token_count = max(1, len(content) // 4)
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            token_count=token_count,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_recent_history(self, session_id: uuid.UUID) -> list[dict[str, str]]:
        messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        # Keep only last N turns (user + assistant pairs)
        tail = messages[-(2 * _HISTORY_TURNS) :]
        return [{"role": m.role, "content": m.content} for m in tail]

    def list_sessions(self) -> list[ChatSession]:
        return (
            self.db.query(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

    def get_session_messages(self, session_id: uuid.UUID) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def build_messages(
        self,
        query: str,
        context: str,
        history: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        context_block = context if context.strip() else "No relevant context was found."
        user_content = f"Context:\n{context_block}\n\nQuestion: {query}"
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_content})
        return messages

    # ------------------------------------------------------------------
    # Streaming generator
    # ------------------------------------------------------------------

    async def stream_answer(
        self,
        query: str,
        session_id: str | None,
        document_ids: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        session = self.get_or_create_session(session_id)
        session_str = str(session.id)

        self.store_message(session.id, role="user", content=query)

        try:
            yield status_event("retrieving context")

            retrieval_service = RetrievalService()
            retrieval_result = retrieval_service.retrieve(
                query=query,
                document_ids=document_ids or None,
                top_k=settings.rerank_top_k,
            )
            context: str = retrieval_result["context"]
            chunks: list[dict[str, Any]] = retrieval_result["chunks"]

            sources = [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "document_id": chunk.get("document_id"),
                    "source_file": chunk.get("source_file"),
                    "page_number": chunk.get("page_number"),
                    "score": chunk.get("rerank_score") or chunk.get("score"),
                }
                for chunk in chunks
            ]

            yield sources_event(sources)
            yield status_event("generating answer")

            history = self.get_recent_history(session.id)
            llm_messages = self.build_messages(query=query, context=context, history=history)

            stream = await self.llm_client.chat.completions.create(
                model=settings.llm_model_name,
                messages=llm_messages,
                stream=True,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )

            full_response: list[str] = []
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response.append(delta)
                    yield token_event(delta)

            answer = "".join(full_response)
            assistant_msg = self.store_message(
                session.id,
                role="assistant",
                content=answer,
                sources=sources,
            )

            # Update session title from first query if not set
            if not session.title:
                session.title = query[:100]
                self.db.commit()

            yield done_event(session_str, str(assistant_msg.id))

        except Exception as exc:
            logger.exception("chat_stream_error", session_id=session_str)
            yield error_event(str(exc))

