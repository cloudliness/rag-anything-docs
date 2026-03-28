from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    knowledge_bases: list[str]
    query_mode: str = "hybrid"
    answer_mode: str = "detailed"


class Citation(BaseModel):
    kb: str
    document: str
    page: int | None = None
    snippet: str
    chunk_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    selected_kbs: list[str]
    contributing_kbs: list[str]
    citations: list[Citation]