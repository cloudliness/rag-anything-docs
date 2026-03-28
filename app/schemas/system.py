from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class DependencyHealthResponse(BaseModel):
    api: str
    parser: str
    storage: str
    llm_backend: str


class CapabilityResponse(BaseModel):
    max_query_kbs: int
    max_upload_target_kbs: int
    multi_kb_query_status: str
    multi_kb_upload_status: str
    kb_creation_enabled: bool
    path_upload_enabled: bool
    math_rendering_status: str
    citation_grounding_status: str
    notes: list[str]