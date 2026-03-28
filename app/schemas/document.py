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
    created_at: str
    updated_at: str
    result: DocumentResponse | None = None
    error: str | None = None
    retry_of: str | None = None
    cancel_requested: bool = False
    can_retry: bool = False
    can_cancel: bool = False