import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.query import QueryRequest, QueryResponse, SourceItem
from app.services import generation, retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "retrieval_ready": retrieval.is_ready()}


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    settings = get_settings()

    try:
        hits = retrieval.retrieve(request.question, project_id=request.project_id, k=settings.top_k)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    project_label = request.project_id or settings.default_project_id

    if not generation.is_grounded_enough(hits, settings):
        logger.info("Grounded refusal for question=%r project=%r", request.question, project_label)
        return QueryResponse(answer=generation.refusal_message(project_label), sources=[], refused=True)

    answer_text = generation.generate(request.question, hits, settings)
    sources = [SourceItem(doc_name=h.doc_name, section=h.section) for h in hits]

    return QueryResponse(answer=answer_text, sources=sources, refused=False)
