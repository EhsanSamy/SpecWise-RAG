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
        # Retrieval service hasn't finished startup yet — shouldn't happen once
        # main.py's lifespan has run, but don't leave the project half-provisioned silently.
        raise HTTPException(status_code=503, detail="Vector store not ready yet — try again shortly.") from e

    logger.info("Provisioned empty collection for project %r (%s)", project["name"], project["id"])
    return ProjectResponse(**project)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    settings = get_settings()
    projects = project_store.list_projects(settings.project_registry_path)
    return [ProjectResponse(**p) for p in projects]
