from fastapi import APIRouter

from app.schemas.system import CapabilityResponse, DependencyHealthResponse, HealthResponse


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.2.0")


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
        max_query_kbs=1,
        max_upload_target_kbs=1,
        multi_kb_query_status="planned",
        multi_kb_upload_status="planned",
        kb_creation_enabled=True,
        path_upload_enabled=True,
        math_rendering_status="planned",
        citation_grounding_status="heuristic",
        notes=[
            "Phase 1 supports one knowledge base per upload and query.",
            "Multi-KB query is planned as query-then-merge in a later slice.",
            "Citation grounding is currently heuristic, not chunk-perfect provenance.",
        ],
    )