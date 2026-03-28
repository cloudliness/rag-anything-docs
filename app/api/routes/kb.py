from fastapi import APIRouter

from app.schemas.kb import CreateKnowledgeBaseRequest, KnowledgeBaseResponse
from app.services.kb_service import create_knowledge_base, list_knowledge_bases


router = APIRouter(prefix="/api/kbs", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
async def get_kbs() -> list[KnowledgeBaseResponse]:
    return list_knowledge_bases()


@router.post("", response_model=KnowledgeBaseResponse)
async def create_kb(payload: CreateKnowledgeBaseRequest) -> KnowledgeBaseResponse:
    return create_knowledge_base(payload)