from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.routes import documents
from app.schemas.document import DocumentResponse
from app.services import ingest_jobs


@pytest.fixture
def isolated_job_store(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_jobs, "_repo_root", lambda: tmp_path)
    ingest_jobs._jobs.clear()
    ingest_jobs._loaded = False
    yield tmp_path
    ingest_jobs._jobs.clear()
    ingest_jobs._loaded = False


def test_job_lifecycle_endpoints(isolated_job_store, monkeypatch):
    source_file = isolated_job_store / "sample.txt"
    source_file.write_text("sample upload body", encoding="utf-8")

    seeded_job = ingest_jobs.create_ingest_job(
        file_name="sample.txt",
        knowledge_base="math_docs",
        source_path=str(source_file),
        parser_backend="mineru",
        parse_method="auto",
        reset=False,
        page=3,
        start_page=None,
        end_page=None,
    )

    async def fake_retry_upload_job(*, background_tasks, job_id: str):
        params = ingest_jobs.get_ingest_job_execution_params(job_id)
        return ingest_jobs.create_ingest_job(
            file_name=params["file_name"],
            knowledge_base=params["knowledge_base"],
            source_path=params["source_path"],
            parser_backend=params["parser_backend"],
            parse_method=params["parse_method"],
            reset=params["reset"],
            page=params["page"],
            start_page=params["start_page"],
            end_page=params["end_page"],
            retry_of=job_id,
        )

    monkeypatch.setattr(documents, "create_retry_upload_job", fake_retry_upload_job)

    client = TestClient(create_app())

    status_response = client.get(f"/api/documents/jobs/{seeded_job.job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["requested_page_count"] == 1
    assert status_response.json()["parser_backend"] == "mineru"

    list_response = client.get("/api/documents/jobs?limit=5")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    cancel_response = client.post(f"/api/documents/jobs/{seeded_job.job_id}/cancel")
    assert cancel_response.status_code == 200
    canceled_job = cancel_response.json()
    assert canceled_job["status"] == "canceled"
    assert canceled_job["duration_ms"] == 0
    assert canceled_job["can_retry"] is True

    retry_response = client.post(f"/api/documents/jobs/{seeded_job.job_id}/retry")
    assert retry_response.status_code == 200
    retried_job = retry_response.json()
    assert retried_job["status"] == "queued"
    assert retried_job["retry_of"] == seeded_job.job_id
    assert retried_job["parser_backend"] == "mineru"
    assert retried_job["can_cancel"] is True

    job_store = isolated_job_store / "knowledge_bases" / "_system" / "ingest_jobs.json"
    assert job_store.exists()


def test_job_filtering_by_knowledge_base(isolated_job_store):
    source_file = isolated_job_store / "sample.txt"
    source_file.write_text("sample upload body", encoding="utf-8")

    ingest_jobs.create_ingest_job(
        file_name="a.txt",
        knowledge_base="math_docs",
        source_path=str(source_file),
        parser_backend="mineru",
        parse_method="auto",
        reset=False,
        page=None,
        start_page=2,
        end_page=4,
    )
    ingest_jobs.create_ingest_job(
        file_name="b.txt",
        knowledge_base="physics_docs",
        source_path=str(source_file),
        parser_backend="mineru",
        parse_method="ocr",
        reset=False,
        page=None,
        start_page=None,
        end_page=None,
    )

    client = TestClient(create_app())
    response = client.get("/api/documents/jobs?kb_name=math_docs&limit=5")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["knowledge_base"] == "math_docs"
    assert jobs[0]["requested_page_count"] == 3


def test_completed_job_exposes_actual_processed_page_telemetry(isolated_job_store):
    source_file = isolated_job_store / "sample.txt"
    source_file.write_text("sample upload body", encoding="utf-8")

    job = ingest_jobs.create_ingest_job(
        file_name="sample.txt",
        knowledge_base="math_docs",
        source_path=str(source_file),
        parser_backend="mineru",
        parse_method="auto",
        reset=False,
        page=None,
        start_page=4,
        end_page=7,
    )

    ingest_jobs.update_ingest_job(job.job_id, status="running", progress=80, message="Finishing")
    ingest_jobs.complete_ingest_job(
        job.job_id,
        DocumentResponse(file_name="sample.txt", knowledge_base="math_docs", status="processed"),
        actual_processed_start_page=5,
        actual_processed_end_page=6,
        actual_processed_page_count=2,
    )

    client = TestClient(create_app())
    response = client.get(f"/api/documents/jobs/{job.job_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["actual_processed_start_page"] == 5
    assert payload["actual_processed_end_page"] == 6
    assert payload["actual_processed_page_count"] == 2
    assert payload["duration_ms"] is not None