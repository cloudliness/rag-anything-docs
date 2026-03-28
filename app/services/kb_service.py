import json
import re
from pathlib import Path

from app.schemas.kb import CreateKnowledgeBaseRequest, KnowledgeBaseResponse


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _kb_root() -> Path:
    return _repo_root() / "knowledge_bases"


def _normalize_kb_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()
    if not normalized:
        raise ValueError("Knowledge base name must contain at least one valid character")
    return normalized


def _metadata_path(kb_dir: Path) -> Path:
    return kb_dir / "metadata.json"


def _read_metadata(kb_dir: Path) -> dict[str, str | None]:
    metadata_path = _metadata_path(kb_dir)
    if not metadata_path.exists():
        return {}
    try:
        with metadata_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        return {}
    return {}


def _write_metadata(kb_dir: Path, payload: dict[str, str | None]) -> None:
    metadata_path = _metadata_path(kb_dir)
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _document_count_for_kb(storage_dir: Path) -> int:
    doc_status_path = storage_dir / "kv_store_doc_status.json"
    if not doc_status_path.exists():
        return 0
    try:
        with doc_status_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return len(data)
    except (json.JSONDecodeError, OSError):
        return 0


def list_knowledge_bases() -> list[KnowledgeBaseResponse]:
    kb_root = _kb_root()
    if not kb_root.exists():
        return []

    responses: list[KnowledgeBaseResponse] = []
    for child in sorted(kb_root.iterdir()):
        if not child.is_dir():
            continue
        storage_dir = child / "storage"
        metadata = _read_metadata(child)
        responses.append(
            KnowledgeBaseResponse(
                name=child.name,
                description=metadata.get("description"),
                document_count=_document_count_for_kb(storage_dir),
            )
        )
    return responses


def create_knowledge_base(payload: CreateKnowledgeBaseRequest) -> KnowledgeBaseResponse:
    normalized_name = _normalize_kb_name(payload.name)
    kb_dir = _kb_root() / normalized_name
    (kb_dir / "storage").mkdir(parents=True, exist_ok=True)
    (kb_dir / "parsed_output").mkdir(parents=True, exist_ok=True)
    _write_metadata(
        kb_dir,
        {
            "name": normalized_name,
            "description": payload.description,
        },
    )
    return KnowledgeBaseResponse(
        name=normalized_name,
        description=payload.description,
        document_count=0,
    )