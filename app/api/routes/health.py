from fastapi import APIRouter


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dependencies")
async def dependency_health() -> dict[str, str]:
    return {
        "api": "ready",
        "parser": "unknown",
        "storage": "unknown",
        "llm_backend": "unknown",
    }