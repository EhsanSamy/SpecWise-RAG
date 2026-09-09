import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services import project_store, retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(request: ProjectCreate) -> ProjectResponse:
    settings = get_settings()

    project = project_store.create_project(settings.project_registry_path, request.name, request.description)

    try:
        chroma_client = retrieval.get_chroma_client()
        chroma_client.get_or_create_collection(name=settings.collection_name(project["id"]))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Vector store not ready yet — try again shortly.") from e

    logger.info("Provisioned empty collection for project %r (%s)", project["name"], project["id"])
    return ProjectResponse(**project)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    settings = get_settings()
    projects = project_store.list_projects(settings.project_registry_path)
    return [ProjectResponse(**p) for p in projects]


@router.delete("/projects/{project_id}")
def delete_project(project_id: str) -> dict:
    settings = get_settings()

    if not project_store.project_exists(settings.project_registry_path, project_id):
        raise HTTPException(status_code=404, detail=f"No project found with id '{project_id}'.")

    # Drop Chroma collection if it exists
    try:
        chroma_client = retrieval.get_chroma_client()
        col_name = settings.collection_name(project_id)
        existing_collections = [c.name for c in chroma_client.list_collections()]
        if col_name in existing_collections:
            chroma_client.delete_collection(name=col_name)
    except Exception as e:
        logger.warning(f"Could not delete Chroma collection for project {project_id}: {e}")

    # Remove from project registry
    deleted = False
    if hasattr(project_store, "delete_project"):
        deleted = project_store.delete_project(settings.project_registry_path, project_id)
    else:
        # Fallback in case project_store only handles read/write
        projects = project_store.list_projects(settings.project_registry_path)
        filtered = [p for p in projects if p.get("id") != project_id]
        if hasattr(project_store, "_save_projects"):
            project_store._save_projects(settings.project_registry_path, filtered)
            deleted = True

    return {"status": "ok", "deleted_project_id": project_id}