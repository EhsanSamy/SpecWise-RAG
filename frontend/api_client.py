import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30


def _handle_response(response: requests.Response) -> dict:
    try:
        response.raise_for_status()
        return {"ok": True, "data": response.json(), "error": None}
    except requests.exceptions.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        return {"ok": False, "data": None, "error": f"{response.status_code}: {detail}"}


def _request(method: str, path: str, **kwargs) -> dict:
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "data": None,
            "error": f"Could not connect to the backend at {API_BASE_URL}. Is it running?",
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "data": None, "error": "The request timed out. The backend may be unreachable."}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "data": None, "error": str(e)}

    return _handle_response(response)


def check_health() -> dict:
    return _request("GET", "/health")


def list_projects() -> dict:
    return _request("GET", "/projects")


def create_project(name: str, description: str | None = None) -> dict:
    payload = {"name": name}
    if description:
        payload["description"] = description
    return _request("POST", "/projects", json=payload)


def delete_project(project_id: str) -> dict:
    return _request("DELETE", f"/projects/{project_id}")


def list_documents(project_id: str) -> dict:
    return _request("GET", f"/projects/{project_id}/documents")


def delete_document(project_id: str, doc_name: str) -> dict:
    safe_doc_name = quote(doc_name, safe="")
    return _request("DELETE", f"/projects/{project_id}/documents/{safe_doc_name}")


def upload_document(project_id: str, filename: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> dict:
    files = {"file": (filename, file_bytes, content_type)}
    return _request("POST", f"/projects/{project_id}/documents", files=files)


def query(question: str, project_id: str | None = None) -> dict:
    payload = {"question": question}
    if project_id:
        payload["project_id"] = project_id
    return _request("POST", "/query", json=payload)


def search(question: str, project_id: str | None = None, k: int | None = None) -> dict:
    payload = {"question": question}
    if project_id:
        payload["project_id"] = project_id
    if k:
        payload["k"] = k
    return _request("POST", "/search", json=payload)