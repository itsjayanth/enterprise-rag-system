from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.chunk import Chunk
from ..models.document import Document
from ..utils.chunking import ChunkPayload, chunk_pages
from ..utils.pdf_parser import parse_document

logger = structlog.get_logger("app.services.ingestion")


class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def process_document(self, document_id: uuid.UUID) -> Document:
        document = self.db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        logger.info("document_processing_started", document_id=str(document.id), filename=document.filename)
        document.status = "processing"
        document.error_message = None
        document.processed_at = None
        self.db.commit()
        self.db.refresh(document)

        start = time.perf_counter()
        try:
            chunks = self.parse_and_chunk(document)
            chunk_count = self.persist_chunks(document.id, chunks)
            document.total_pages = max((chunk.page_number or 0) for chunk in chunks) if chunks else 0
            document.total_chunks = chunk_count
            document.status = "chunked"
            document.error_message = None
            document.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(document)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("document_processing_failed", document_id=str(document.id))
            document.status = "failed"
            document.error_message = str(exc)
            document.processed_at = None
            self.db.commit()
            self.db.refresh(document)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document.",
            ) from exc

        logger.info(
            "document_processing_completed",
            document_id=str(document.id),
            total_chunks=document.total_chunks,
            total_pages=document.total_pages,
            duration_seconds=round(time.perf_counter() - start, 4),
        )
        return document

    def parse_and_chunk(self, document: Document) -> list[ChunkPayload]:
        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found at {file_path}")

        pages = parse_document(file_path, document.file_type)
        if not pages:
            raise ValueError("No text could be extracted from the document")
        return chunk_pages(pages, source_file=document.filename)

    def persist_chunks(self, document_id: uuid.UUID, chunks: list[ChunkPayload]) -> int:
        self.db.query(Chunk).filter(Chunk.document_id == document_id).delete()

        for chunk in chunks:
            self.db.add(
                Chunk(
                    document_id=document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    char_count=chunk.char_count,
                    token_count=chunk.token_count,
                    chunk_metadata=chunk.chunk_metadata,
                )
            )

        self.db.commit()
        return len(chunks)

