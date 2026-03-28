#!/usr/bin/env python

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from raganything import RAGAnything, RAGAnythingConfig


def ensure_v1(base_url: str) -> str:
    return base_url if base_url.rstrip("/").endswith("/v1") else f"{base_url.rstrip('/')}/v1"


async def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env", override=False)
    env_bin = str(Path(sys.executable).resolve().parent)
    os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"

    llm_model = os.environ["LLM_MODEL"]
    llm_base_url = ensure_v1(os.environ["LLM_BINDING_HOST"])
    llm_api_key = os.getenv("LLM_BINDING_API_KEY", "ollama")

    embedding_model = os.environ["EMBEDDING_MODEL"]
    embedding_dim = int(os.environ["EMBEDDING_DIM"])
    embedding_base_url = ensure_v1(os.environ["EMBEDDING_BINDING_HOST"])
    embedding_api_key = os.getenv("EMBEDDING_BINDING_API_KEY", "ollama")

    config = RAGAnythingConfig(
        working_dir=str(repo_root / "rag_storage_ollama_smoke"),
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

    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
    )

    sample_file = repo_root / "examples" / "sample_note.md"
    output_dir = repo_root / "test_output" / "ollama_smoke"

    await rag.process_document_complete(
        file_path=str(sample_file),
        output_dir=str(output_dir),
        parse_method="auto",
    )

    answer = await rag.aquery(
        "What is the name of the conda environment mentioned in the document? Reply with only the environment name.",
        mode="hybrid",
    )
    print("OLLAMA_SMOKE_RESULT:", answer)


if __name__ == "__main__":
    asyncio.run(main())