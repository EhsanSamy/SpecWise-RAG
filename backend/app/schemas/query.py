from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The natural-language question to answer.")
    project_id: str | None = Field(
        default=None,
        description="Which project's document collection to query. Omit to use the default/global collection.",
    )


class SourceItem(BaseModel):
    doc_name: str
    section: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)
    refused: bool = False
