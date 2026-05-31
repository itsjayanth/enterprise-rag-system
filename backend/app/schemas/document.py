from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    total_pages: int | None
    total_chunks: int | None
    created_at: datetime
    updated_at: datetime


class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    error_message: str | None
    total_pages: int | None
    total_chunks: int | None
    processed_at: datetime | None


class DocumentProcessResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str

