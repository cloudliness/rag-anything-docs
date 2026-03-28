from fastapi import APIRouter

from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import run_query


router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    return await run_query(payload)