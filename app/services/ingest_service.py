import asyncio
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from app.schemas.document import DocumentResponse, UploadDocumentRequest
from raganything import RAGAnything, RAGAnythingConfig


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


def _resolve_page_bounds(payload: UploadDocumentRequest) -> tuple[int | None, int | None]:
    if payload.page is not None and (payload.start_page is not None or payload.end_page is not None):
        raise HTTPException(status_code=400, detail="Use either page or start_page/end_page, not both")
    if payload.page is not None:
        if payload.page < 1:
            raise HTTPException(status_code=400, detail="page must be 1 or greater")
        zero_based = payload.page - 1
        return zero_based, zero_based
    if payload.start_page is None and payload.end_page is None:
        return None, None
    if payload.start_page is None:
        raise HTTPException(status_code=400, detail="end_page requires start_page")
    if payload.start_page < 1:
        raise HTTPException(status_code=400, detail="start_page must be 1 or greater")
    if payload.end_page is not None and payload.end_page < payload.start_page:
        raise HTTPException(status_code=400, detail="end_page must be greater than or equal to start_page")
    return payload.start_page - 1, None if payload.end_page is None else payload.end_page - 1


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
    start_page, end_page = _resolve_page_bounds(payload)
    kb_paths = _kb_paths(kb_name)
    if payload.reset:
        for key in ("storage", "output"):
            target = kb_paths[key]
            if target.exists():
                for child in target.iterdir():
                    if child.is_dir():
                        import shutil
                        shutil.rmtree(child)
                    else:
                        child.unlink()

    rag = _create_rag(kb_name)
    kb_paths["output"].mkdir(parents=True, exist_ok=True)
    parser_kwargs = {}
    if start_page is not None:
        parser_kwargs["start_page"] = start_page
    if end_page is not None:
        parser_kwargs["end_page"] = end_page

    await rag.process_document_complete(
        file_path=str(source_path),
        output_dir=str(kb_paths["output"]),
        parse_method=payload.parse_method or os.getenv("PARSE_METHOD", "auto"),
        **parser_kwargs,
    )

    return DocumentResponse(
        file_name=source_path.name,
        knowledge_base=kb_name,
        status="processed",
        parsed_output_path=str(kb_paths["output"]),
    )