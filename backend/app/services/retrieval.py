import logging
from dataclasses import dataclass

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from app.core.config import Settings

logger = logging.getLogger(__name__)

_chroma_client: chromadb.ClientAPI | None = None
_embedding_model: SentenceTransformer | None = None
_settings: Settings | None = None


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_name: str
    section: str | None
    text: str
    distance: float


def init_retrieval(settings: Settings) -> None:
    """Load the Chroma client and the embedding model once. Call this from
    the FastAPI lifespan startup handler — never from inside a request."""
    global _chroma_client, _embedding_model, _settings

    logger.info("Loading Chroma client from %s", settings.vector_store_dir)
    _chroma_client = chromadb.PersistentClient(path=str(settings.vector_store_dir))

    logger.info("Loading embedding model %s", settings.embedding_model_name)
    _embedding_model = SentenceTransformer(settings.embedding_model_name)

    _settings = settings
    logger.info("Retrieval service ready.")


def is_ready() -> bool:
    return _chroma_client is not None and _embedding_model is not None


def get_embedding_model() -> SentenceTransformer:
    if _embedding_model is None:
        raise RuntimeError("Retrieval service not initialized — call init_retrieval() at startup first.")
    return _embedding_model


def get_chroma_client() -> chromadb.ClientAPI:
    if _chroma_client is None:
        raise RuntimeError("Retrieval service not initialized — call init_retrieval() at startup first.")
    return _chroma_client


def _get_collection(project_id: str | None) -> Collection:
    if _chroma_client is None or _settings is None:
        raise RuntimeError("Retrieval service not initialized — call init_retrieval() at startup first.")

    collection_name = _settings.collection_name(project_id)
    try:
        return _chroma_client.get_collection(name=collection_name)
    except Exception as e:
        raise LookupError(
            f"No collection found for '{collection_name}'. "
            f"Has this project's documents been ingested yet?"
        ) from e


def retrieve(question: str, project_id: str | None = None, k: int | None = None) -> list[RetrievedChunk]:
    if _embedding_model is None or _settings is None:
        raise RuntimeError("Retrieval service not initialized — call init_retrieval() at startup first.")

    collection = _get_collection(project_id)
    top_k = k or _settings.top_k

    query_embedding = _embedding_model.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    if not results["ids"] or not results["ids"][0]:
        return []

    chunks = []
    for chunk_id, doc, meta, dist in zip(
        results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                doc_name=meta.get("doc_name", "unknown"),
                section=meta.get("section") or None,
                text=doc,
                distance=dist,
            )
        )
    return chunks