from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.schemas.document import DocumentResponse, IngestJobResponse, UploadDocumentRequest
from app.services.ingest_jobs import cancel_ingest_job, get_ingest_job, list_ingest_jobs
from app.services.ingest_service import create_browser_upload_job, create_retry_upload_job, upload_browser_file, upload_document
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


@router.post("/upload-jobs", response_model=IngestJobResponse)
async def upload_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    knowledge_base: str = Form(...),
    parse_method: str | None = Form(None),
    reset: bool = Form(False),
    page: int | None = Form(None),
    start_page: int | None = Form(None),
    end_page: int | None = Form(None),
) -> IngestJobResponse:
    return await create_browser_upload_job(
        background_tasks=background_tasks,
        file=file,
        knowledge_base=knowledge_base,
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
    )


@router.get("/jobs/{job_id}", response_model=IngestJobResponse)
async def ingest_job_status(job_id: str) -> IngestJobResponse:
    return get_ingest_job(job_id)


@router.get("/jobs", response_model=list[IngestJobResponse])
async def ingest_jobs(kb_name: str | None = None, limit: int = 25) -> list[IngestJobResponse]:
    return list_ingest_jobs(knowledge_base=kb_name, limit=limit)


@router.post("/jobs/{job_id}/cancel", response_model=IngestJobResponse)
async def cancel_job(job_id: str) -> IngestJobResponse:
    return cancel_ingest_job(job_id)


@router.post("/jobs/{job_id}/retry", response_model=IngestJobResponse)
async def retry_job(job_id: str, background_tasks: BackgroundTasks) -> IngestJobResponse:
    return await create_retry_upload_job(background_tasks=background_tasks, job_id=job_id)


@router.get("/kb/{kb_name}", response_model=list[DocumentResponse])
async def list_documents(kb_name: str) -> list[DocumentResponse]:
    return list_documents_for_kb(kb_name)