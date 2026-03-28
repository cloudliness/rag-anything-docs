from fastapi import APIRouter

from app.schemas.system import CapabilityResponse, DependencyHealthResponse, HealthResponse


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.4.0")


@router.get("/dependencies", response_model=DependencyHealthResponse)
async def dependency_health() -> DependencyHealthResponse:
    return DependencyHealthResponse(
        api="ready",
        parser="configured",
        storage="filesystem",
        llm_backend="configured",
    )


@router.get("/capabilities", response_model=CapabilityResponse)
async def capability_health() -> CapabilityResponse:
    return CapabilityResponse(
        max_query_kbs=8,
        max_upload_target_kbs=1,
        multi_kb_query_status="enabled",
        multi_kb_upload_status="planned",
        background_ingest_status="enabled",
        kb_creation_enabled=True,
        path_upload_enabled=False,
        browser_upload_enabled=True,
        math_rendering_status="enabled",
        citation_grounding_status="chunk-backed",
        notes=[
            "Phase 1 supports one knowledge base per upload.",
            "Multi-KB query is enabled using per-KB retrieval followed by answer synthesis.",
            "The product UI now uses browser-based multipart upload and polls ingest job progress.",
            "Citation grounding now prefers stored text chunks over document summaries.",
        ],
    )