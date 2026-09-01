from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import AuditLogOut
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{request_id}", response_model=list[AuditLogOut])
def get_audit_logs(request_id: int, db: Session = Depends(get_db)):
    return audit_service.get_audit_logs_for_request(db, request_id)
