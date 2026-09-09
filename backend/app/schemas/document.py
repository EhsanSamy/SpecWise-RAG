from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str  # "ok" | "failed"
    chunks_added: int = 0
    error: str | None = None
