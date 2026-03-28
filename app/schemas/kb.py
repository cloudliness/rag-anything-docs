from pydantic import BaseModel


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str | None = None


class KnowledgeBaseResponse(BaseModel):
    name: str
    description: str | None = None
    document_count: int = 0