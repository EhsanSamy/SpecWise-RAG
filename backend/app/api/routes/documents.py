import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.document import DocumentUploadResponse
from app.services import ingestion, project_store

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
