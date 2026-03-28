import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.document import DocumentResponse, IngestJobResponse


_job_lock = Lock()
_jobs: dict[str, dict] = {}
_loaded = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _job_store_path() -> Path:
    return _repo_root() / "knowledge_bases" / "_system" / "ingest_jobs.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_loaded() -> None:
    global _loaded

    with _job_lock:
        if _loaded:
            return

        store_path = _job_store_path()
        if store_path.exists():
            try:
                with store_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    for job_id, job in payload.items():
                        if isinstance(job, dict):
                            _jobs[job_id] = job
            except (json.JSONDecodeError, OSError):
                _jobs.clear()

        _loaded = True


def _persist_jobs_locked() -> None:
    store_path = _job_store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("w", encoding="utf-8") as handle:
        json.dump(_jobs, handle, indent=2, sort_keys=True)


def _job_can_retry(job: dict) -> bool:
    return job.get("status") in {"completed", "failed", "canceled"}


def _job_can_cancel(job: dict) -> bool:
    return job.get("status") in {"queued", "running"} and not bool(job.get("cancel_requested"))


def _to_response(job: dict) -> IngestJobResponse:
    result = job.get("result")
    return IngestJobResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=int(job.get("progress", 0)),
        message=job.get("message", ""),
        knowledge_base=job["knowledge_base"],
        file_name=job["file_name"],
        created_at=job.get("created_at", _now_iso()),
        updated_at=job.get("updated_at", _now_iso()),
        result=DocumentResponse.model_validate(result) if result else None,
        error=job.get("error"),
        retry_of=job.get("retry_of"),
        cancel_requested=bool(job.get("cancel_requested", False)),
        can_retry=_job_can_retry(job),
        can_cancel=_job_can_cancel(job),
    )


def _require_job_locked(job_id: str) -> dict:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Ingest job '{job_id}' was not found")
    return _jobs[job_id]


def create_ingest_job(
    *,
    file_name: str,
    knowledge_base: str,
    source_path: str,
    parse_method: str | None,
    reset: bool,
    page: int | None,
    start_page: int | None,
    end_page: int | None,
    retry_of: str | None = None,
) -> IngestJobResponse:
    _ensure_loaded()
    timestamp = _now_iso()
    job = {
        "job_id": uuid4().hex,
        "status": "queued",
        "progress": 0,
        "message": "Upload accepted and waiting to start.",
        "knowledge_base": knowledge_base,
        "file_name": file_name,
        "created_at": timestamp,
        "updated_at": timestamp,
        "result": None,
        "error": None,
        "retry_of": retry_of,
        "cancel_requested": False,
        "source_path": source_path,
        "parse_method": parse_method,
        "reset": reset,
        "page": page,
        "start_page": start_page,
        "end_page": end_page,
    }
    with _job_lock:
        _jobs[job["job_id"]] = job
        _persist_jobs_locked()
        return _to_response(job)


def update_ingest_job(job_id: str, *, status: str | None = None, progress: int | None = None, message: str | None = None) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        if status is not None:
            job["status"] = status
        if progress is not None:
            job["progress"] = max(0, min(100, progress))
        if message is not None:
            job["message"] = message
        job["updated_at"] = _now_iso()
        _persist_jobs_locked()
        return _to_response(job)


def complete_ingest_job(job_id: str, result: DocumentResponse) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = "Document ingest completed."
        job["result"] = result.model_dump()
        job["error"] = None
        job["cancel_requested"] = False
        job["updated_at"] = _now_iso()
        _persist_jobs_locked()
        return _to_response(job)


def fail_ingest_job(job_id: str, error: str) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        job["status"] = "failed"
        job["progress"] = 100
        job["message"] = "Document ingest failed."
        job["error"] = error
        job["updated_at"] = _now_iso()
        _persist_jobs_locked()
        return _to_response(job)


def cancel_ingest_job(job_id: str) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        if job["status"] == "queued":
            job["status"] = "canceled"
            job["message"] = "Ingest job canceled before processing started."
            job["cancel_requested"] = False
            job["updated_at"] = _now_iso()
            _persist_jobs_locked()
            return _to_response(job)
        if job["status"] == "running":
            job["cancel_requested"] = True
            job["message"] = "Cancellation requested. Processing will stop at the next safe checkpoint."
            job["updated_at"] = _now_iso()
            _persist_jobs_locked()
            return _to_response(job)
        raise HTTPException(status_code=409, detail=f"Ingest job '{job_id}' is already in terminal state '{job['status']}'")


def mark_ingest_job_canceled(job_id: str, message: str) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        job["status"] = "canceled"
        job["message"] = message
        job["cancel_requested"] = False
        job["updated_at"] = _now_iso()
        _persist_jobs_locked()
        return _to_response(job)


def is_cancel_requested(job_id: str) -> bool:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        return bool(job.get("cancel_requested", False)) or job.get("status") == "canceled"


def get_ingest_job(job_id: str) -> IngestJobResponse:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        return _to_response(job)


def list_ingest_jobs(*, knowledge_base: str | None = None, limit: int = 25) -> list[IngestJobResponse]:
    _ensure_loaded()
    with _job_lock:
        jobs = list(_jobs.values())

    if knowledge_base:
        jobs = [job for job in jobs if job.get("knowledge_base") == knowledge_base]

    jobs.sort(key=lambda job: (job.get("updated_at", ""), job.get("created_at", "")), reverse=True)
    return [_to_response(job) for job in jobs[: max(limit, 1)]]


def get_ingest_job_execution_params(job_id: str) -> dict:
    _ensure_loaded()
    with _job_lock:
        job = _require_job_locked(job_id)
        return {
            "file_name": job["file_name"],
            "knowledge_base": job["knowledge_base"],
            "source_path": job["source_path"],
            "parse_method": job.get("parse_method"),
            "reset": bool(job.get("reset", False)),
            "page": job.get("page"),
            "start_page": job.get("start_page"),
            "end_page": job.get("end_page"),
        }