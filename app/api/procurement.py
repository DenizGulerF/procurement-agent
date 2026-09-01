from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import ProcurementRequestOut
from app.services import procurement_service, user_service

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.get("/requests", response_model=list[ProcurementRequestOut])
def list_requests(db: Session = Depends(get_db)):
    return procurement_service.list_procurement_requests(db)


@router.get("/requests/{request_id}", response_model=ProcurementRequestOut)
def get_request(request_id: int, db: Session = Depends(get_db)):
    req = procurement_service.get_procurement_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found.")
    return req


@router.post("/requests/{request_id}/approve", response_model=ProcurementRequestOut)
def approve_request(
    request_id: int,
    acting_user_id: int = Query(..., description="ID of the user performing the approval"),
    db: Session = Depends(get_db),
):
    acting_user = user_service.get_user(db, acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found.")
    return procurement_service.approve_procurement_request(db, request_id, acting_user)


@router.post("/requests/{request_id}/reject", response_model=ProcurementRequestOut)
def reject_request(
    request_id: int,
    acting_user_id: int = Query(..., description="ID of the user performing the rejection"),
    db: Session = Depends(get_db),
):
    acting_user = user_service.get_user(db, acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found.")
    return procurement_service.reject_procurement_request(db, request_id, acting_user)
