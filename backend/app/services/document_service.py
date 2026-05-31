from __future__ import annotations

import re
import uuid
from pathlib import Path

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import ROOT_DIR, settings
from ..models.document import Document

logger = structlog.get_logger("app.services.document")

_ALLOWED_EXTENSIONS = {".pdf": "pdf", ".txt": "txt"}
_ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
}
_FILENAME_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_CHUNK_SIZE = 1024 * 1024


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_root = self._resolve_upload_root()

    def list_documents(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def get_document(self, document_id: uuid.UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def upload_document(self, file: UploadFile) -> Document:
        logger.info("document_upload_started", filename=file.filename, content_type=file.content_type)
        self.validate_file(file)

        document_id = uuid.uuid4()
        destination = self.build_storage_path(document_id, file.filename or "upload")

        try:
            file_size = self.save_upload(file, destination)
            document = self.create_document_record(
                document_id=document_id,
                filename=file.filename or destination.name,
                file_size=file_size,
                file_type=self.detect_file_type(file.filename or destination.name),
                storage_path=str(destination),
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception("document_upload_failed", filename=file.filename)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file.",
            )
        finally:
            file.file.close()

        logger.info("document_upload_succeeded", document_id=str(document.id), filename=document.filename)
        return document

    def validate_file(self, file: UploadFile) -> None:
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()

        if extension not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only PDF and TXT are allowed.",
            )

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in _ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported MIME type. Only PDF and TXT uploads are allowed.",
            )

    def build_storage_path(self, document_id: uuid.UUID, filename: str) -> Path:
        sanitized = self._sanitize_filename(filename)
        extension = Path(sanitized).suffix.lower()
        directory = self.upload_root / "default" / str(document_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"original{extension}"

    def save_upload(self, file: UploadFile, destination: Path) -> int:
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        total_size = 0

        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size_bytes:
                    output.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Max allowed size is {settings.max_upload_size_mb} MB.",
                    )
                output.write(chunk)

        if total_size == 0:
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        return total_size

    def create_document_record(
        self,
        *,
        document_id: uuid.UUID,
        filename: str,
        file_size: int,
        file_type: str,
        storage_path: str,
    ) -> Document:
        document = Document(
            id=document_id,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            storage_path=storage_path,
            status="uploaded",
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def _resolve_upload_root(self) -> Path:
        configured = Path(settings.upload_dir)
        if configured.is_absolute():
            return configured
        docker_upload_root = Path("/data/uploads")
        if configured.as_posix().endswith("data/uploads") and docker_upload_root.exists():
            return docker_upload_root
        return ROOT_DIR / configured

    @staticmethod
    def detect_file_type(filename: str) -> str:
        extension = Path(filename).suffix.lower()
        return _ALLOWED_EXTENSIONS[extension]

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        cleaned = _FILENAME_SAFE_CHARS.sub("-", Path(filename).name).strip(".-")
        return cleaned or "upload"

