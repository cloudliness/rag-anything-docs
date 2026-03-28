import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, HTTPException, UploadFile
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from app.schemas.document import DocumentResponse, UploadDocumentRequest
from app.services.ingest_jobs import (
    complete_ingest_job,
    create_ingest_job,
    fail_ingest_job,
    get_ingest_job,
    get_ingest_job_execution_params,
    is_cancel_requested,
    mark_ingest_job_canceled,
    update_ingest_job,
)
from raganything import RAGAnything, RAGAnythingConfig


class IngestJobCanceledError(Exception):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalize_kb_name(kb_name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", kb_name.strip()).strip("-").lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Knowledge base name must contain valid characters")
    return normalized


def _ensure_v1(base_url: str) -> str:
    return base_url if base_url.rstrip("/").endswith("/v1") else f"{base_url.rstrip('/')}/v1"


def _load_environment() -> None:
    root = _repo_root()
    load_dotenv(root / ".env", override=False)
    env_bin = str(Path(sys.executable).resolve().parent)
    os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"


def _resolve_page_bounds(
    page: int | None,
    start_page: int | None,
    end_page: int | None,
) -> tuple[int | None, int | None]:
    if page is not None and (start_page is not None or end_page is not None):
        raise HTTPException(status_code=400, detail="Use either page or start_page/end_page, not both")
    if page is not None:
        if page < 1:
            raise HTTPException(status_code=400, detail="page must be 1 or greater")
        zero_based = page - 1
        return zero_based, zero_based
    if start_page is None and end_page is None:
        return None, None
    if start_page is None:
        raise HTTPException(status_code=400, detail="end_page requires start_page")
    if start_page < 1:
        raise HTTPException(status_code=400, detail="start_page must be 1 or greater")
    if end_page is not None and end_page < start_page:
        raise HTTPException(status_code=400, detail="end_page must be greater than or equal to start_page")
    return start_page - 1, None if end_page is None else end_page - 1


def _default_runtime_options() -> dict[str, int]:
    llm_binding = os.getenv("LLM_BINDING", "").lower()
    is_ollama = llm_binding == "ollama"
    def env_int(name: str, default: int) -> int:
        value = os.getenv(name)
        return int(value) if value is not None and value != "" else default
    return {
        "llm_timeout": env_int("MANUALS_LLM_TIMEOUT", 900 if is_ollama else 180),
        "llm_max_async": env_int("MANUALS_LLM_MAX_ASYNC", 1 if is_ollama else 4),
        "max_parallel_insert": env_int("MANUALS_MAX_PARALLEL_INSERT", 1 if is_ollama else 2),
        "chunk_token_size": env_int("MANUALS_CHUNK_TOKEN_SIZE", 800 if is_ollama else 1200),
        "chunk_overlap_token_size": env_int("MANUALS_CHUNK_OVERLAP_TOKEN_SIZE", 100),
        "max_extract_input_tokens": env_int("MANUALS_MAX_EXTRACT_INPUT_TOKENS", 12000 if is_ollama else 20480),
    }


def _kb_paths(kb_name: str) -> dict[str, Path]:
    root = _repo_root()
    normalized = _normalize_kb_name(kb_name)
    return {
        "name": Path(normalized),
        "storage": root / "knowledge_bases" / normalized / "storage",
        "output": root / "knowledge_bases" / normalized / "parsed_output",
        "uploads": root / "knowledge_bases" / normalized / "source_uploads",
    }


def _create_rag(kb_name: str) -> RAGAnything:
    runtime_options = _default_runtime_options()
    paths = _kb_paths(kb_name)
    llm_model = os.environ["LLM_MODEL"]
    llm_base_url = _ensure_v1(os.environ["LLM_BINDING_HOST"])
    llm_api_key = os.getenv("LLM_BINDING_API_KEY", "ollama")

    embedding_model = os.environ["EMBEDDING_MODEL"]
    embedding_dim = int(os.environ["EMBEDDING_DIM"])
    embedding_base_url = _ensure_v1(os.environ["EMBEDDING_BINDING_HOST"])
    embedding_api_key = os.getenv("EMBEDDING_BINDING_API_KEY", "ollama")

    config = RAGAnythingConfig(
        working_dir=str(paths["storage"]),
        parser=os.getenv("PARSER", "mineru"),
        parse_method=os.getenv("PARSE_METHOD", "auto"),
        enable_image_processing=False,
        enable_table_processing=True,
        enable_equation_processing=True,
    )

    def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return openai_complete_if_cache(
            llm_model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=llm_api_key,
            base_url=llm_base_url,
            **kwargs,
        )

    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,
        func=lambda texts: openai_embed.func(
            texts,
            model=embedding_model,
            api_key=embedding_api_key,
            base_url=embedding_base_url,
        ),
    )

    return RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs={
            "default_llm_timeout": runtime_options["llm_timeout"],
            "llm_model_max_async": runtime_options["llm_max_async"],
            "max_parallel_insert": runtime_options["max_parallel_insert"],
            "chunk_token_size": runtime_options["chunk_token_size"],
            "chunk_overlap_token_size": runtime_options["chunk_overlap_token_size"],
            "max_extract_input_tokens": runtime_options["max_extract_input_tokens"],
        },
    )


def _reset_knowledge_base(kb_paths: dict[str, Path]) -> None:
    for key in ("storage", "output"):
        target = kb_paths[key]
        if not target.exists():
            continue
        for child in target.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def _persist_uploaded_file(upload_file: UploadFile, kb_name: str) -> Path:
    kb_paths = _kb_paths(kb_name)
    kb_paths["uploads"].mkdir(parents=True, exist_ok=True)

    original_name = Path(upload_file.filename or "uploaded-document").name
    safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", Path(original_name).stem).strip(".-") or "uploaded-document"
    suffix = Path(original_name).suffix
    destination = kb_paths["uploads"] / f"{safe_stem}{suffix}"

    if destination.exists():
        destination = kb_paths["uploads"] / f"{safe_stem}-{uuid4().hex[:8]}{suffix}"

    upload_file.file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload_file.file, handle)

    return destination


def _report_progress(progress_callback: Callable[[int, str], None] | None, progress: int, message: str) -> None:
    if progress_callback is not None:
        progress_callback(progress, message)


def _raise_if_job_canceled(job_id: str, message: str) -> None:
    if is_cancel_requested(job_id):
        raise IngestJobCanceledError(message)


async def _process_document(
    *,
    source_path: Path,
    kb_name: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
    display_name: str | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> DocumentResponse:
    _report_progress(progress_callback, 10, "Validating document options.")
    start_page_value, end_page_value = _resolve_page_bounds(page, start_page, end_page)
    kb_paths = _kb_paths(kb_name)
    if reset:
        _report_progress(progress_callback, 20, "Resetting existing knowledge base storage.")
        _reset_knowledge_base(kb_paths)

    _report_progress(progress_callback, 35, "Preparing retrieval engine.")
    rag = _create_rag(kb_name)
    kb_paths["output"].mkdir(parents=True, exist_ok=True)
    parser_kwargs = {}
    if start_page_value is not None:
        parser_kwargs["start_page"] = start_page_value
    if end_page_value is not None:
        parser_kwargs["end_page"] = end_page_value

    _report_progress(progress_callback, 60, "Parsing and indexing document content.")
    await rag.process_document_complete(
        file_path=str(source_path),
        output_dir=str(kb_paths["output"]),
        parse_method=parse_method or os.getenv("PARSE_METHOD", "auto"),
        **parser_kwargs,
    )

    _report_progress(progress_callback, 90, "Finalizing ingest metadata.")

    return DocumentResponse(
        file_name=display_name or source_path.name,
        knowledge_base=kb_name,
        status="processed",
        parsed_output_path=str(kb_paths["output"]),
    )


async def upload_document(payload: UploadDocumentRequest) -> DocumentResponse:
    if not payload.knowledge_bases:
        raise HTTPException(status_code=400, detail="At least one knowledge base must be provided")
    if len(payload.knowledge_bases) != 1:
        raise HTTPException(status_code=400, detail="Phase 1 upload supports a single target knowledge base")

    _load_environment()
    source_path = Path(payload.source_path).expanduser().resolve()
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {source_path}")

    kb_name = _normalize_kb_name(payload.knowledge_bases[0])
    return await _process_document(
        source_path=source_path,
        kb_name=kb_name,
        parse_method=payload.parse_method,
        reset=payload.reset,
        page=payload.page,
        start_page=payload.start_page,
        end_page=payload.end_page,
    )


async def upload_browser_file(
    *,
    file: UploadFile,
    knowledge_base: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
) -> DocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file must be provided")

    _load_environment()
    kb_name = _normalize_kb_name(knowledge_base)
    persisted_path = _persist_uploaded_file(file, kb_name)
    return await _process_document(
        source_path=persisted_path,
        kb_name=kb_name,
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
        display_name=file.filename,
    )


async def _run_browser_upload_job(
    *,
    job_id: str,
    source_path: Path,
    file_name: str,
    knowledge_base: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
) -> None:
    try:
        _raise_if_job_canceled(job_id, "Ingest job canceled before processing started.")
        update_ingest_job(job_id, status="running", progress=5, message="Background ingest started.")
        _raise_if_job_canceled(job_id, "Ingest job canceled before parsing started.")
        result = await _process_document(
            source_path=source_path,
            kb_name=knowledge_base,
            parse_method=parse_method,
            reset=reset,
            page=page,
            start_page=start_page,
            end_page=end_page,
            display_name=file_name,
            progress_callback=lambda progress, message: update_ingest_job(job_id, status="running", progress=progress, message=message),
        )
        complete_ingest_job(job_id, result)
    except IngestJobCanceledError as exc:
        mark_ingest_job_canceled(job_id, str(exc))
    except Exception as exc:
        fail_ingest_job(job_id, str(exc))


def _schedule_upload_job(
    *,
    background_tasks: BackgroundTasks,
    job_id: str,
    source_path: Path,
    file_name: str,
    knowledge_base: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
) -> None:
    background_tasks.add_task(
        _run_browser_upload_job,
        job_id=job_id,
        source_path=source_path,
        file_name=file_name,
        knowledge_base=knowledge_base,
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
    )


async def create_browser_upload_job(
    *,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    knowledge_base: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file must be provided")

    _load_environment()
    kb_name = _normalize_kb_name(knowledge_base)
    persisted_path = _persist_uploaded_file(file, kb_name)
    job = create_ingest_job(
        file_name=file.filename,
        knowledge_base=kb_name,
        source_path=str(persisted_path),
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
    )
    update_ingest_job(job.job_id, status="queued", progress=5, message="Upload received and queued for ingest.")
    _schedule_upload_job(
        background_tasks=background_tasks,
        job_id=job.job_id,
        source_path=persisted_path,
        file_name=file.filename,
        knowledge_base=kb_name,
        parse_method=parse_method,
        reset=reset,
        page=page,
        start_page=start_page,
        end_page=end_page,
    )
    return get_ingest_job(job.job_id)


async def create_retry_upload_job(*, background_tasks: BackgroundTasks, job_id: str):
    _load_environment()
    params = get_ingest_job_execution_params(job_id)
    source_path = Path(params["source_path"]).expanduser().resolve()
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Retry source file not found: {source_path}")

    job = create_ingest_job(
        file_name=params["file_name"],
        knowledge_base=params["knowledge_base"],
        source_path=str(source_path),
        parse_method=params["parse_method"],
        reset=bool(params["reset"]),
        page=params["page"],
        start_page=params["start_page"],
        end_page=params["end_page"],
        retry_of=job_id,
    )
    update_ingest_job(job.job_id, status="queued", progress=5, message="Retry queued for ingest.")
    _schedule_upload_job(
        background_tasks=background_tasks,
        job_id=job.job_id,
        source_path=source_path,
        file_name=params["file_name"],
        knowledge_base=params["knowledge_base"],
        parse_method=params["parse_method"],
        reset=bool(params["reset"]),
        page=params["page"],
        start_page=params["start_page"],
        end_page=params["end_page"],
    )
    return get_ingest_job(job.job_id)