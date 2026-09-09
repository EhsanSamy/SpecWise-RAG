import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services import retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    settings = get_settings()

    try:
        hits = retrieval.retrieve(request.question, project_id=request.project_id, k=request.k or settings.top_k)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    results = [
        SearchResult(doc_name=h.doc_name, section=h.section, text=h.text, distance=h.distance) for h in hits
    ]
    return SearchResponse(results=results)