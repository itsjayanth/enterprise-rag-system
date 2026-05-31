from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .pdf_parser import ParsedPage


@dataclass(slots=True)
class ChunkPayload:
    chunk_index: int
    content: str
    page_number: int | None
    char_count: int
    token_count: int | None
    chunk_metadata: dict


_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def estimate_token_count(text: str) -> int:
    return max(1, len(text.split()))


def chunk_pages(pages: list[ParsedPage], source_file: str) -> list[ChunkPayload]:
    chunks: list[ChunkPayload] = []
    chunk_index = 0
    source_name = Path(source_file).name

    for page in pages:
        split_texts = _SPLITTER.split_text(page.text)
        for content in split_texts:
            clean_content = content.strip()
            if not clean_content:
                continue
            chunks.append(
                ChunkPayload(
                    chunk_index=chunk_index,
                    content=clean_content,
                    page_number=page.page_number,
                    char_count=len(clean_content),
                    token_count=estimate_token_count(clean_content),
                    chunk_metadata={
                        "page_number": page.page_number,
                        "source_file": source_name,
                        "chunk_index": chunk_index,
                        "char_count": len(clean_content),
                    },
                )
            )
            chunk_index += 1

    return chunks

