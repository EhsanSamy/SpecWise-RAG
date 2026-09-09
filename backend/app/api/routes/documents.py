import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.document import DocumentUploadResponse
from app.services import ingestion, project_store, retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects/{project_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(project_id: str, file: UploadFile = File(...)) -> DocumentUploadResponse:
    settings = get_settings()

    if not project_store.project_exists(settings.project_registry_path, project_id):
        raise HTTPException(status_code=404, detail=f"No project found with id '{project_id}'.")

    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        result = ingestion.ingest_document(project_id, tmp_path, file.filename or "unnamed", settings)
    finally:
        tmp_path.unlink(missing_ok=True)

    if result["status"] == "ok" and result["chunks_added"] > 0:
        project_store.increment_document_count(settings.project_registry_path, project_id)
    else:
        logger.warning("Upload to project %s did not ingest cleanly: %s", project_id, result.get("error"))

    return DocumentUploadResponse(**result)


@router.get("/projects/{project_id}/documents")
def list_project_documents(project_id: str) -> list[dict]:
    settings = get_settings()
    if not project_store.project_exists(settings.project_registry_path, project_id):
        raise HTTPException(status_code=404, detail=f"No project found with id '{project_id}'.")

    try:
        chroma_client = retrieval.get_chroma_client()
        col = chroma_client.get_collection(name=settings.collection_name(project_id))
        data = col.get(include=["metadatas"])
    except Exception as e:
        logger.warning(f"Failed to query collection for project {project_id}: {e}")
        return []

    doc_counts: dict[str, int] = {}
    for meta in data.get("metadatas", []):
        if meta and "doc_name" in meta:
            name = meta["doc_name"]
            doc_counts[name] = doc_counts.get(name, 0) + 1

    return [{"name": name, "chunk_count": count} for name, count in doc_counts.items()]


@router.delete("/projects/{project_id}/documents/{doc_name}")
def delete_project_document(project_id: str, doc_name: str) -> dict:
    settings = get_settings()
    if not project_store.project_exists(settings.project_registry_path, project_id):
        raise HTTPException(status_code=404, detail=f"No project found with id '{project_id}'.")

    try:
        chroma_client = retrieval.get_chroma_client()
        col = chroma_client.get_collection(name=settings.collection_name(project_id))
        col.delete(where={"doc_name": doc_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document chunks: {e}")

    # Decrement document count if helper exists
    if hasattr(project_store, "decrement_document_count"):
        project_store.decrement_document_count(settings.project_registry_path, project_id)

    return {"status": "ok", "deleted_document": doc_name}