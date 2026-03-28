from pydantic import BaseModel


class UploadDocumentRequest(BaseModel):
    source_path: str
    knowledge_bases: list[str]
    parse_method: str | None = None
    reset: bool = False
    page: int | None = None
    start_page: int | None = None
    end_page: int | None = None


class DocumentResponse(BaseModel):
    file_name: str
    knowledge_base: str
    status: str
    parsed_output_path: str | None = None


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    knowledge_base: str
    file_name: str
    parser_backend: str
    parse_method: str | None = None
    requested_page: int | None = None
    requested_start_page: int | None = None
    requested_end_page: int | None = None
    requested_page_count: int | None = None
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    result: DocumentResponse | None = None
    error: str | None = None
    retry_of: str | None = None
    cancel_requested: bool = False
    can_retry: bool = False
    can_cancel: bool = False