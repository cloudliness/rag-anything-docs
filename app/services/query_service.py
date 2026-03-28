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


MAX_QUERY_KBS = 8


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


def _llm_settings() -> dict[str, str]:
    return {
        "model": os.environ["LLM_MODEL"],
        "base_url": _ensure_v1(os.environ["LLM_BINDING_HOST"]),
        "api_key": os.getenv("LLM_BINDING_API_KEY", "ollama"),
    }


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


def _load_text_chunks(kb_name: str) -> dict:
    text_chunks_path = _repo_root() / "knowledge_bases" / kb_name / "storage" / "kv_store_text_chunks.json"
    if not text_chunks_path.exists():
        return {}
    try:
        with text_chunks_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _score_overlap(query: str, content: str) -> int:
    query_terms = {term for term in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(term) >= 3}
    if not query_terms:
        return 0
    content_terms = re.findall(r"[a-zA-Z0-9]+", content.lower())
    return sum(1 for term in content_terms if term in query_terms)


def _best_page_for_chunk(doc_id: str, chunk_content: str, parse_cache: dict) -> int | None:
    normalized_chunk_content = _normalize_text(chunk_content)
    best_score = -1
    best_page: int | None = None

    for entry in parse_cache.values():
        if entry.get("doc_id") != doc_id:
            continue
        for item in entry.get("content_list", []):
            item_text = str(item.get("text", "")).strip()
            if not item_text:
                continue
            normalized_item_text = _normalize_text(item_text)
            if normalized_item_text and normalized_item_text in normalized_chunk_content:
                try:
                    return int(item.get("page_idx")) + 1
                except (TypeError, ValueError):
                    return None
            score = _score_overlap(normalized_chunk_content, item_text)
            if score > best_score:
                best_score = score
                try:
                    best_page = int(item.get("page_idx")) + 1
                except (TypeError, ValueError):
                    best_page = None

    return best_page


def _excerpt(text: str, limit: int = 320) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


def _chunk_backed_citations(question: str, kb_name: str, doc_id: str, doc_record: dict, text_chunks: dict, parse_cache: dict) -> list[Citation]:
    chunk_candidates: list[tuple[int, str, dict]] = []
    for chunk_id in doc_record.get("chunks_list", []):
        chunk = text_chunks.get(chunk_id)
        if not chunk:
            continue
        score = _score_overlap(question, str(chunk.get("content", "")))
        chunk_candidates.append((score, chunk_id, chunk))

    chunk_candidates.sort(key=lambda item: item[0], reverse=True)
    selected_chunks = chunk_candidates[:2] if chunk_candidates else []
    citations: list[Citation] = []

    for _, chunk_id, chunk in selected_chunks:
        chunk_content = str(chunk.get("content", "")).strip()
        citations.append(
            Citation(
                kb=kb_name,
                document=str(doc_record.get("file_path", "unknown")),
                page=_best_page_for_chunk(doc_id, chunk_content, parse_cache),
                snippet=_excerpt(chunk_content),
                chunk_id=chunk_id,
            )
        )

    return citations


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


def _citations_from_answer(question: str, kb_name: str, answer: str) -> list[Citation]:
    doc_status_map = _load_doc_status_map(kb_name)
    parse_cache = _load_parse_cache(kb_name)
    text_chunks = _load_text_chunks(kb_name)
    references = _extract_reference_documents(answer)
    citations: list[Citation] = []

    if references:
        for reference in references:
            matched_doc_id = None
            matched_doc = None
            for doc_id, item in doc_status_map.items():
                if item.get("file_path") == reference:
                    matched_doc_id = doc_id
                    matched_doc = item
                    break

            if matched_doc is None or matched_doc_id is None:
                continue

            chunk_citations = _chunk_backed_citations(question, kb_name, matched_doc_id, matched_doc, text_chunks, parse_cache)
            if chunk_citations:
                citations.extend(chunk_citations)
                break

    if citations:
        return citations

    scored_docs: list[tuple[int, str, dict]] = []
    for doc_id, doc_record in doc_status_map.items():
        score = 0
        for chunk_id in doc_record.get("chunks_list", []):
            chunk = text_chunks.get(chunk_id)
            if not chunk:
                continue
            score = max(score, _score_overlap(question, str(chunk.get("content", ""))))
        scored_docs.append((score, doc_id, doc_record))

    scored_docs.sort(key=lambda item: item[0], reverse=True)
    for _, doc_id, doc_record in scored_docs[:2]:
        citations.extend(_chunk_backed_citations(question, kb_name, doc_id, doc_record, text_chunks, parse_cache))

    return citations


def _normalize_selected_kbs(selected_kbs: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for kb_name in selected_kbs:
        normalized_name = _normalize_kb_name(kb_name)
        if normalized_name in seen:
            continue
        seen.add(normalized_name)
        normalized.append(normalized_name)

    if not normalized:
        raise HTTPException(status_code=400, detail="At least one knowledge base must be selected")
    if len(normalized) > MAX_QUERY_KBS:
        raise HTTPException(status_code=400, detail=f"A maximum of {MAX_QUERY_KBS} knowledge bases can be queried at once")

    return normalized


async def _run_query_for_kb(kb_name: str, question: str, query_mode: str) -> dict:
    rag = _create_rag(kb_name)
    await rag._ensure_lightrag_initialized()
    answer = await rag.aquery(question, mode=query_mode)
    return {
        "kb_name": kb_name,
        "answer": answer.strip(),
        "citations": _citations_from_answer(question, kb_name, answer),
    }


def _dedupe_citations(citations: list[Citation]) -> list[Citation]:
    deduped: list[Citation] = []
    seen: set[tuple[str, str, int | None, str]] = set()

    for citation in citations:
        key = (citation.kb, citation.document, citation.page, citation.snippet)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(citation)

    return deduped


async def _merge_query_results(question: str, answer_mode: str, kb_results: list[dict]) -> str:
    llm_settings = _llm_settings()
    result_sections: list[str] = []

    for result in kb_results:
        citation_lines: list[str] = []
        for citation in result["citations"][:5]:
            page_text = f", page {citation.page}" if citation.page else ""
            citation_lines.append(f"- {citation.document}{page_text}: {citation.snippet}")
        citation_summary = "\n".join(citation_lines) or "- No structured citations were extracted for this KB."
        result_sections.append(
            f"## Knowledge Base: {result['kb_name']}\n"
            f"Draft answer:\n{result['answer'] or 'No answer returned.'}\n\n"
            f"Extracted citations:\n{citation_summary}"
        )

    merged_result_sections = "\n\n".join(result_sections)

    merge_prompt = (
        "Combine the following knowledge-base-specific answers into one final markdown answer.\n"
        "Use only the provided drafts and citation summaries.\n"
        "If different KBs disagree, say that clearly instead of inventing a reconciliation.\n"
        f"Target answer style: {answer_mode}.\n\n"
        f"User question:\n{question}\n\n"
        "Knowledge-base results:\n\n"
        f"{merged_result_sections}"
    )

    return await openai_complete_if_cache(
        llm_settings["model"],
        merge_prompt,
        system_prompt="You are a retrieval answer synthesizer. Return a single clear markdown answer grounded only in the provided drafts.",
        history_messages=[],
        api_key=llm_settings["api_key"],
        base_url=llm_settings["base_url"],
    )


async def run_query(payload: QueryRequest) -> QueryResponse:
    _load_environment()
    selected_kbs = _normalize_selected_kbs(payload.knowledge_bases)
    kb_results: list[dict] = []

    for kb_name in selected_kbs:
        kb_results.append(await _run_query_for_kb(kb_name, payload.question, payload.query_mode))

    if len(kb_results) == 1:
        final_answer = kb_results[0]["answer"]
    else:
        final_answer = await _merge_query_results(payload.question, payload.answer_mode, kb_results)

    citations = _dedupe_citations(
        [citation for result in kb_results for citation in result["citations"]]
    )
    contributing_kbs = [result["kb_name"] for result in kb_results if result["answer"] or result["citations"]]

    return QueryResponse(
        answer=final_answer,
        selected_kbs=selected_kbs,
        contributing_kbs=contributing_kbs,
        citations=citations,
    )