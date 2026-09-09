from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The text to search for related chunks.")
    project_id: str | None = Field(
        default=None,
        description="Which project's document collection to search. Omit to use the default/global collection.",
    )
    k: int | None = Field(default=None, description="How many results to return. Falls back to the configured TOP_K.")


class SearchResult(BaseModel):
    doc_name: str
    section: str | None = None
    text: str
    distance: float


class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(default_factory=list)