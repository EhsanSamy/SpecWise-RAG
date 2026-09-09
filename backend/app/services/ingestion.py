import logging
import re
import uuid
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.services import retrieval

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

logger = logging.getLogger(__name__)

HEADER_PATTERN = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


class ParseError(Exception):
    """Raised when a file can't be parsed into usable text at all."""


class EmptyDocumentError(Exception):
    """Raised when parsing succeeds but yields no extractable text
    (e.g. a scanned PDF with no text layer) — distinct from ParseError
    so the caller can give a more specific message."""


# --- Parse -----------------------------------------------------------------
def parse(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ParseError(f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_SUFFIXES)}")

    try:
        if suffix in (".md", ".txt"):
            return path.read_text(encoding="utf-8")
        else:  # .pdf
            if not PYPDF_AVAILABLE:
                raise ParseError("pypdf is not installed — run `uv add pypdf`.")
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse '{path.name}': {e}") from e


# --- Clean -------------------------------------------------------------------
def clean(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


# --- Chunk ------------------------------------------------------------------
def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    matches = list(HEADER_PATTERN.finditer(text))
    if not matches:
        return [(None, text.strip())]
    sections = []
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _sliding_word_windows(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if len(words) <= size:
        return [words]
    windows = []
    step = size - overlap
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            break
        windows.append(window)
        if start + size >= len(words):
            break
    return windows


def chunk_document(doc_name: str, text: str, settings: Settings) -> list[dict[str, Any]]:
    chunks = []
    for heading, body in _split_into_sections(text):
        words = body.split()
        if len(words) <= settings.chunk_size_words:
            chunks.append({"doc_name": doc_name, "section": heading, "text": body})
        else:
            for window in _sliding_word_windows(words, settings.chunk_size_words, settings.chunk_overlap_words):
                chunks.append({"doc_name": doc_name, "section": heading, "text": " ".join(window)})
    return chunks


# --- Embed + store ------------------------------------------------------------
def embed_and_store(project_id: str, chunks: list[dict[str, Any]], settings: Settings) -> int:
    if not chunks:
        return 0

    embedding_model = retrieval.get_embedding_model()
    chroma_client = retrieval.get_chroma_client()

    collection_name = settings.collection_name(project_id)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    texts = [c["text"] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()

    upload_tag = uuid.uuid4().hex[:8]
    ids = [f"{c['doc_name']}::{upload_tag}::{i}" for i, c in enumerate(chunks)]
    metadatas = [{"doc_name": c["doc_name"], "section": c["section"] or ""} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    logger.info("Added %d chunks to collection '%s'", len(chunks), collection_name)
    return len(chunks)


# --- Orchestration ------------------------------------------------------------
def ingest_document(project_id: str, file_path: Path, original_filename: str, settings: Settings) -> dict[str, Any]:
    try:
        raw_text = parse(file_path)
    except ParseError as e:
        return {"filename": original_filename, "status": "failed", "chunks_added": 0, "error": str(e)}

    text = clean(raw_text)
    if not text.strip():
        return {
            "filename": original_filename,
            "status": "failed",
            "chunks_added": 0,
            "error": "No extractable text found — the file may be a scanned image needing OCR.",
        }

    chunks = chunk_document(original_filename, text, settings)
    if not chunks:
        return {
            "filename": original_filename,
            "status": "failed",
            "chunks_added": 0,
            "error": "Document produced no chunks after processing.",
        }

    try:
        added = embed_and_store(project_id, chunks, settings)
    except Exception as e:
        logger.error("Embedding/storage failed for '%s': %s", original_filename, e)
        return {"filename": original_filename, "status": "failed", "chunks_added": 0, "error": str(e)}

    return {"filename": original_filename, "status": "ok", "chunks_added": added, "error": None}