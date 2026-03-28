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