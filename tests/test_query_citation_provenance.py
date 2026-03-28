import json

from app.services import query_service


def test_chunk_backed_citations_include_page_and_chunk_id(tmp_path, monkeypatch):
    monkeypatch.setattr(query_service, "_repo_root", lambda: tmp_path)

    storage_dir = tmp_path / "knowledge_bases" / "math_docs" / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    doc_status = {
        "doc-1": {
            "file_path": "math1.pdf",
            "chunks_list": ["chunk-1", "chunk-2"],
            "content_summary": "Derivative examples",
        }
    }
    text_chunks = {
        "chunk-1": {
            "content": "Derivative of x squared is two x. The tangent line slope comes from the derivative at a point.",
            "file_path": "math1.pdf",
            "full_doc_id": "doc-1",
            "chunk_order_index": 0,
        },
        "chunk-2": {
            "content": "Integrals accumulate signed area under a curve.",
            "file_path": "math1.pdf",
            "full_doc_id": "doc-1",
            "chunk_order_index": 1,
        },
    }
    parse_cache = {
        "parse-1": {
            "doc_id": "doc-1",
            "content_list": [
                {
                    "text": "Derivative of x squared is two x. The tangent line slope comes from the derivative at a point.",
                    "page_idx": 3,
                }
            ],
        }
    }

    (storage_dir / "kv_store_doc_status.json").write_text(json.dumps(doc_status), encoding="utf-8")
    (storage_dir / "kv_store_text_chunks.json").write_text(json.dumps(text_chunks), encoding="utf-8")
    (storage_dir / "kv_store_parse_cache.json").write_text(json.dumps(parse_cache), encoding="utf-8")

    citations = query_service._citations_from_answer(
        "How do tangent line slopes use derivatives?",
        "math_docs",
        "Summary\n\nReferences\n- [1] math1.pdf",
    )

    assert len(citations) >= 1
    assert citations[0].document == "math1.pdf"
    assert citations[0].page == 4
    assert citations[0].chunk_id == "chunk-1"
    assert "tangent line slope" in citations[0].snippet.lower()