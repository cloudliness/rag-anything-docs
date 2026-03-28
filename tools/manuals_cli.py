#!/usr/bin/env python

import argparse
import asyncio
import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from raganything import RAGAnything, RAGAnythingConfig


def ensure_v1(base_url: str) -> str:
    return base_url if base_url.rstrip("/").endswith("/v1") else f"{base_url.rstrip('/')}/v1"


def normalize_kb_name(kb_name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", kb_name.strip()).strip("-").lower()
    if not normalized:
        raise ValueError("Knowledge base name must contain at least one valid character")
    return normalized


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_environment() -> None:
    root = repo_root()
    load_dotenv(root / ".env", override=False)
    env_bin = str(Path(sys.executable).resolve().parent)
    os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None and value != "" else default


def kb_paths(kb_name: str) -> dict[str, Path]:
    root = repo_root()
    normalized = normalize_kb_name(kb_name)
    return {
        "name": Path(normalized),
        "storage": root / "knowledge_bases" / normalized / "storage",
        "output": root / "knowledge_bases" / normalized / "parsed_output",
    }


def default_runtime_options() -> dict[str, int]:
    llm_binding = os.getenv("LLM_BINDING", "").lower()
    is_ollama = llm_binding == "ollama"
    return {
        "llm_timeout": env_int("MANUALS_LLM_TIMEOUT", 900 if is_ollama else 180),
        "llm_max_async": env_int("MANUALS_LLM_MAX_ASYNC", 1 if is_ollama else 4),
        "max_parallel_insert": env_int("MANUALS_MAX_PARALLEL_INSERT", 1 if is_ollama else 2),
        "chunk_token_size": env_int("MANUALS_CHUNK_TOKEN_SIZE", 800 if is_ollama else 1200),
        "chunk_overlap_token_size": env_int("MANUALS_CHUNK_OVERLAP_TOKEN_SIZE", 100),
        "max_extract_input_tokens": env_int("MANUALS_MAX_EXTRACT_INPUT_TOKENS", 12000 if is_ollama else 20480),
    }


def resolve_runtime_options(args) -> dict[str, int]:
    defaults = default_runtime_options()
    return {
        "llm_timeout": args.llm_timeout if getattr(args, "llm_timeout", None) is not None else defaults["llm_timeout"],
        "llm_max_async": args.llm_max_async if getattr(args, "llm_max_async", None) is not None else defaults["llm_max_async"],
        "max_parallel_insert": args.max_parallel_insert if getattr(args, "max_parallel_insert", None) is not None else defaults["max_parallel_insert"],
        "chunk_token_size": args.chunk_token_size if getattr(args, "chunk_token_size", None) is not None else defaults["chunk_token_size"],
        "chunk_overlap_token_size": args.chunk_overlap_token_size if getattr(args, "chunk_overlap_token_size", None) is not None else defaults["chunk_overlap_token_size"],
        "max_extract_input_tokens": args.max_extract_input_tokens if getattr(args, "max_extract_input_tokens", None) is not None else defaults["max_extract_input_tokens"],
    }


def resolve_page_bounds(args) -> tuple[int | None, int | None]:
    page = getattr(args, "page", None)
    start_page = getattr(args, "start_page", None)
    end_page = getattr(args, "end_page", None)

    if page is not None and (start_page is not None or end_page is not None):
        raise ValueError("Use either --page or --start-page/--end-page, not both")

    if page is not None:
        if page < 1:
            raise ValueError("--page must be 1 or greater")
        zero_based_page = page - 1
        return zero_based_page, zero_based_page

    if start_page is None and end_page is None:
        return None, None

    if start_page is None:
        raise ValueError("--end-page requires --start-page")

    if start_page < 1:
        raise ValueError("--start-page must be 1 or greater")

    if end_page is not None and end_page < 1:
        raise ValueError("--end-page must be 1 or greater")

    if end_page is not None and end_page < start_page:
        raise ValueError("--end-page must be greater than or equal to --start-page")

    return start_page - 1, None if end_page is None else end_page - 1


def reset_kb(kb_name: str) -> None:
    paths = kb_paths(kb_name)
    for key in ("storage", "output"):
        target = paths[key]
        if target.exists():
            shutil.rmtree(target)


def create_rag(kb_name: str, runtime_options: dict[str, int] | None = None) -> RAGAnything:
    paths = kb_paths(kb_name)
    runtime_options = runtime_options or default_runtime_options()

    llm_model = os.environ["LLM_MODEL"]
    llm_base_url = ensure_v1(os.environ["LLM_BINDING_HOST"])
    llm_api_key = os.getenv("LLM_BINDING_API_KEY", "ollama")

    embedding_model = os.environ["EMBEDDING_MODEL"]
    embedding_dim = int(os.environ["EMBEDDING_DIM"])
    embedding_base_url = ensure_v1(os.environ["EMBEDDING_BINDING_HOST"])
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


async def ingest_documents(
    kb_name: str,
    files: list[str],
    parse_method: str | None,
    runtime_options: dict[str, int],
    reset: bool,
    start_page: int | None,
    end_page: int | None,
) -> int:
    if reset:
        reset_kb(kb_name)

    rag = create_rag(kb_name, runtime_options)
    paths = kb_paths(kb_name)
    paths["output"].mkdir(parents=True, exist_ok=True)

    print(f"KB_NAME: {normalize_kb_name(kb_name)}")
    print(f"LLM_TIMEOUT: {runtime_options['llm_timeout']}")
    print(f"LLM_MAX_ASYNC: {runtime_options['llm_max_async']}")
    print(f"MAX_PARALLEL_INSERT: {runtime_options['max_parallel_insert']}")
    print(f"CHUNK_TOKEN_SIZE: {runtime_options['chunk_token_size']}")
    print(f"CHUNK_OVERLAP_TOKEN_SIZE: {runtime_options['chunk_overlap_token_size']}")
    print(f"MAX_EXTRACT_INPUT_TOKENS: {runtime_options['max_extract_input_tokens']}")
    if start_page is not None:
        human_end_page = start_page + 1 if end_page is None else end_page + 1
        print(f"PAGE_RANGE: {start_page + 1}-{human_end_page}")

    for raw_file in files:
        file_path = Path(raw_file).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        print(f"INGESTING: {file_path}")
        parser_kwargs = {}
        if start_page is not None:
            parser_kwargs["start_page"] = start_page
        if end_page is not None:
            parser_kwargs["end_page"] = end_page
        await rag.process_document_complete(
            file_path=str(file_path),
            output_dir=str(paths["output"]),
            parse_method=parse_method or os.getenv("PARSE_METHOD", "auto"),
            **parser_kwargs,
        )
        print(f"INGESTED: {file_path.name}")

    print(f"KB_READY: {normalize_kb_name(kb_name)}")
    print(f"KB_STORAGE: {paths['storage']}")
    print(f"KB_PARSED_OUTPUT: {paths['output']}")
    return 0


async def query_kb(kb_name: str, question: str, mode: str) -> int:
    rag = create_rag(kb_name)
    await rag._ensure_lightrag_initialized()
    print(f"QUERY_KB: {normalize_kb_name(kb_name)}")
    print(f"QUERY_MODE: {mode}")
    print(f"QUESTION: {question}")
    answer = await rag.aquery(question, mode=mode)
    print("ANSWER_START")
    print(answer)
    print("ANSWER_END")
    return 0


def list_kbs() -> int:
    base_dir = repo_root() / "knowledge_bases"
    if not base_dir.exists():
        print("No knowledge bases found.")
        return 0

    found_any = False
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir():
            continue
        found_any = True
        print(child.name)

    if not found_any:
        print("No knowledge bases found.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manuals knowledge base CLI for local Ollama-backed RAG-Anything")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Parse and index one or more documents into a knowledge base")
    ingest_parser.add_argument("--kb", required=True, help="Knowledge base name, e.g. auto_manuals")
    ingest_parser.add_argument("files", nargs="+", help="One or more document paths to ingest")
    ingest_parser.add_argument("--parse-method", choices=["auto", "ocr", "txt"], help="Override parse method for this run")
    ingest_parser.add_argument("--reset", action="store_true", help="Delete the existing KB storage and parsed output before ingesting")
    ingest_parser.add_argument("--page", type=int, help="Ingest exactly one 1-based page from each input document")
    ingest_parser.add_argument("--start-page", type=int, help="1-based start page for page-bounded ingest")
    ingest_parser.add_argument("--end-page", type=int, help="1-based end page for page-bounded ingest")
    ingest_parser.add_argument("--llm-timeout", type=int, help="Per-call LLM timeout in seconds for indexing")
    ingest_parser.add_argument("--llm-max-async", type=int, help="Max concurrent LLM calls during indexing")
    ingest_parser.add_argument("--max-parallel-insert", type=int, help="Max concurrent insert workers")
    ingest_parser.add_argument("--chunk-token-size", type=int, help="Chunk size used for text splitting")
    ingest_parser.add_argument("--chunk-overlap-token-size", type=int, help="Chunk overlap used for text splitting")
    ingest_parser.add_argument("--max-extract-input-tokens", type=int, help="Upper bound for entity extraction input tokens")

    query_parser = subparsers.add_parser("query", help="Query an existing knowledge base")
    query_parser.add_argument("--kb", required=True, help="Knowledge base name, e.g. auto_manuals")
    query_parser.add_argument("--mode", default="hybrid", choices=["hybrid", "local", "global", "naive"], help="Query mode")
    query_parser.add_argument("question", help="Question to ask")

    subparsers.add_parser("list-kbs", help="List available knowledge bases")
    return parser


async def async_main() -> int:
    load_environment()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        start_page, end_page = resolve_page_bounds(args)
        return await ingest_documents(
            args.kb,
            args.files,
            args.parse_method,
            resolve_runtime_options(args),
            args.reset,
            start_page,
            end_page,
        )
    if args.command == "query":
        return await query_kb(args.kb, args.question, args.mode)
    if args.command == "list-kbs":
        return list_kbs()

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))