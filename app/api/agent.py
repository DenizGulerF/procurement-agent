from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import AgentRequest, AgentResponse
from app.services.user_service import get_user
from app.agent.service import run_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/request", response_model=AgentResponse)
def agent_request(body: AgentRequest, db: Session = Depends(get_db)):
    user = get_user(db, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {body.user_id} not found.")

    result = run_agent(db=db, user_id=body.user_id, message=body.message)
    return AgentResponse(
        response=result["response"],
        tool_calls=result["tool_calls"],
    )
