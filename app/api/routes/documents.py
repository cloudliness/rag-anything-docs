from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.document import DocumentResponse, UploadDocumentRequest
from app.services.ingest_service import upload_browser_file, upload_document
from app.services.storage_service import list_documents_for_kb


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload(payload: UploadDocumentRequest) -> DocumentResponse:
    return await upload_document(payload)


@router.post("/upload-file", response_model=DocumentResponse)
async def upload_file(
    file: UploadFile = File(...),
    knowledge_base: str = Form(...),
    parse_method: str | None = Form(None),
    reset: bool = Form(False),
    page: int | None = Form(None),
    start_page: int | None = Form(None),
    end_page: int | None = Form(None),
) -> DocumentResponse:
    return await upload_browser_file(
        file=file,
        knowledge_base=knowledge_base,
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
    )


@router.get("/kb/{kb_name}", response_model=list[DocumentResponse])
async def list_documents(kb_name: str) -> list[DocumentResponse]:
    return list_documents_for_kb(kb_name)