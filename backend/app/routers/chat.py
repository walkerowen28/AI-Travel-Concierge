from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.runner import run_concierge
from app.db import get_db
from app.schemas_chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    result = await run_concierge(
        db,
        messages=[message.model_dump() for message in body.messages],
        reservation_id=body.reservation_id,
    )
    return ChatResponse(**result)
