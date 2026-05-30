from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
import structlog

logger = structlog.get_logger("app.utils.pdf_parser")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def parse_pdf(file_path: str | Path) -> list[ParsedPage]:
    path = Path(file_path)
    start = time.perf_counter()
    document = pdfium.PdfDocument(str(path))
    parsed_pages: list[ParsedPage] = []

    try:
        for page_index in range(len(document)):
            page = document[page_index]
            text_page = page.get_textpage()
            text = normalize_whitespace(text_page.get_text_range())
            text_page.close()
            page.close()
            if text:
                parsed_pages.append(ParsedPage(page_number=page_index + 1, text=text))
    finally:
        document.close()

    duration = round(time.perf_counter() - start, 4)
    logger.info(
        "pdf_parsed",
        file_path=str(path),
        page_count=len(parsed_pages),
        duration_seconds=duration,
    )
    if not parsed_pages:
        logger.warning("pdf_parsed_with_no_text", file_path=str(path))
    return parsed_pages


def parse_txt(file_path: str | Path) -> list[ParsedPage]:
    path = Path(file_path)
    start = time.perf_counter()
    text = normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))
    duration = round(time.perf_counter() - start, 4)
    logger.info("txt_parsed", file_path=str(path), duration_seconds=duration, char_count=len(text))
    return [ParsedPage(page_number=1, text=text)] if text else []


def parse_document(file_path: str | Path, file_type: str) -> list[ParsedPage]:
    if file_type == "pdf":
        return parse_pdf(file_path)
    if file_type == "txt":
        return parse_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")

