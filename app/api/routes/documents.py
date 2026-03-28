from fastapi import APIRouter

from app.schemas.document import DocumentResponse, UploadDocumentRequest
from app.services.ingest_service import upload_document
from app.services.storage_service import list_documents_for_kb


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload(payload: UploadDocumentRequest) -> DocumentResponse:
    return await upload_document(payload)


@router.get("/kb/{kb_name}", response_model=list[DocumentResponse])
async def list_documents(kb_name: str) -> list[DocumentResponse]:
    return list_documents_for_kb(kb_name)