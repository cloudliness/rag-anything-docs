import json
from pathlib import Path

from app.schemas.document import DocumentResponse


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _kb_storage_dir(kb_name: str) -> Path:
    return _repo_root() / "knowledge_bases" / kb_name / "storage"


def list_documents_for_kb(kb_name: str) -> list[DocumentResponse]:
    doc_status_path = _kb_storage_dir(kb_name) / "kv_store_doc_status.json"
    if not doc_status_path.exists():
        return []

    try:
        with doc_status_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []

    documents: list[DocumentResponse] = []
    for item in data.values():
        documents.append(
            DocumentResponse(
                file_name=item.get("file_path", "unknown"),
                knowledge_base=kb_name,
                status=item.get("status", "unknown"),
            )
        )
    return documents