from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health, kb, query


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Pipeline Product API",
        version="0.5.0",
        description="Phase 1 scaffold for the product-facing API layer.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(kb.router)
    app.include_router(documents.router)
    app.include_router(query.router)
    return app


app = create_app()