import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load(registry_path: Path) -> dict[str, Any]:
    if not registry_path.exists():
        return {"projects": {}}
    try:
        return json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Project registry at %s is corrupt: %s", registry_path, e)
        raise


def _save(registry_path: Path, data: dict[str, Any]) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_project(registry_path: Path, name: str, description: str | None = None) -> dict[str, Any]:
    data = _load(registry_path)

    project_id = uuid.uuid4().hex[:12]
    project = {
        "id": project_id,
        "name": name,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "document_count": 0,
    }
    data["projects"][project_id] = project
    _save(registry_path, data)

    logger.info("Created project %r (%s)", name, project_id)
    return project


def get_project(registry_path: Path, project_id: str) -> dict[str, Any] | None:
    data = _load(registry_path)
    return data["projects"].get(project_id)


def list_projects(registry_path: Path) -> list[dict[str, Any]]:
    data = _load(registry_path)
    return list(data["projects"].values())


def project_exists(registry_path: Path, project_id: str) -> bool:
    return get_project(registry_path, project_id) is not None


def increment_document_count(registry_path: Path, project_id: str, by: int = 1) -> dict[str, Any]:
    data = _load(registry_path)
    project = data["projects"].get(project_id)
    if project is None:
        raise LookupError(f"No project found with id '{project_id}'.")

    project["document_count"] += by
    data["projects"][project_id] = project
    _save(registry_path, data)
    return project
