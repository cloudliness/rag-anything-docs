import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from app.schemas.query import Citation, QueryRequest, QueryResponse
from raganything import RAGAnything, RAGAnythingConfig


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalize_kb_name(kb_name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", kb_name.strip()).strip("-").lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Knowledge base name is invalid")
    return normalized


def _ensure_v1(base_url: str) -> str:
    return base_url if base_url.rstrip("/").endswith("/v1") else f"{base_url.rstrip('/')}/v1"


def _load_environment() -> None:
    root = _repo_root()
    load_dotenv(root / ".env", override=False)
    env_bin = str(Path(sys.executable).resolve().parent)
    os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"


def _create_rag(kb_name: str) -> RAGAnything:
    normalized_name = _normalize_kb_name(kb_name)
    working_dir = _repo_root() / "knowledge_bases" / normalized_name / "storage"
    if not working_dir.exists():
        raise HTTPException(status_code=404, detail=f"Knowledge base '{normalized_name}' was not found")

    llm_model = os.environ["LLM_MODEL"]
    llm_base_url = _ensure_v1(os.environ["LLM_BINDING_HOST"])
    llm_api_key = os.getenv("LLM_BINDING_API_KEY", "ollama")

    embedding_model = os.environ["EMBEDDING_MODEL"]
    embedding_dim = int(os.environ["EMBEDDING_DIM"])
    embedding_base_url = _ensure_v1(os.environ["EMBEDDING_BINDING_HOST"])
    embedding_api_key = os.getenv("EMBEDDING_BINDING_API_KEY", "ollama")

    config = RAGAnythingConfig(
        working_dir=str(working_dir),
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
    )


def _extract_reference_documents(answer: str) -> list[str]:
    matches = re.findall(r"- \[\d+\] ([^\n]+)", answer)
    return [match.strip() for match in matches]


def _load_doc_status_map(kb_name: str) -> dict:
    doc_status_path = _repo_root() / "knowledge_bases" / kb_name / "storage" / "kv_store_doc_status.json"
    if not doc_status_path.exists():
        return {}
    try:
        with doc_status_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def _load_parse_cache(kb_name: str) -> dict:
    parse_cache_path = _repo_root() / "knowledge_bases" / kb_name / "storage" / "kv_store_parse_cache.json"
    if not parse_cache_path.exists():
        return {}
    try:
        with parse_cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def _page_number_from_content_list(content_list: list[dict]) -> int | None:
    for item in content_list:
        if item.get("type") == "page_number":
            text = str(item.get("text", "")).strip()
            if text.isdigit():
                return int(text)
    for item in content_list:
        if "page_idx" in item:
            try:
                return int(item["page_idx"]) + 1
            except (TypeError, ValueError):
                return None
    return None


def _citations_from_answer(kb_name: str, answer: str) -> list[Citation]:
    doc_status_map = _load_doc_status_map(kb_name)
    parse_cache = _load_parse_cache(kb_name)
    references = _extract_reference_documents(answer)
    if not references:
        return []

    citations: list[Citation] = []
    for reference in references:
        matched_doc = None
        for item in doc_status_map.values():
            if item.get("file_path") == reference:
                matched_doc = item
                break

        snippet = None
        page = None
        if matched_doc is not None:
            snippet = matched_doc.get("content_summary")

        for entry in parse_cache.values():
            if entry.get("doc_id") and matched_doc is not None and entry.get("doc_id") == next((key for key, value in doc_status_map.items() if value is matched_doc), None):
                content_list = entry.get("content_list", [])
                page = _page_number_from_content_list(content_list)
                if not snippet:
                    for item in content_list:
                        if item.get("type") == "text" and item.get("text"):
                            snippet = str(item["text"]).strip()
                            break
                break

        citations.append(
            Citation(
                kb=kb_name,
                document=reference,
                page=page,
                snippet=snippet or "Source document matched from the query reference list.",
            )
        )
    return citations


async def run_query(payload: QueryRequest) -> QueryResponse:
    selected_kbs = payload.knowledge_bases
    if not selected_kbs:
        raise HTTPException(status_code=400, detail="At least one knowledge base must be selected")
    if len(selected_kbs) != 1:
        raise HTTPException(status_code=400, detail="Phase 1 query only supports a single knowledge base")

    _load_environment()
    kb_name = _normalize_kb_name(selected_kbs[0])
    rag = _create_rag(kb_name)
    await rag._ensure_lightrag_initialized()
    answer = await rag.aquery(payload.question, mode=payload.query_mode)
    citations = _citations_from_answer(kb_name, answer)

    return QueryResponse(
        answer=answer,
        selected_kbs=[kb_name],
        contributing_kbs=[kb_name],
        citations=citations,
    )