"""Procurement service — create, read, approve, reject requests."""

from datetime import datetime, timezone, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import (
    ProcurementRequest,
    ProcurementStatus,
    ProcurementPriority,
    UserRole,
    User,
)


def create_procurement_request(
    db: Session,
    user_id: int,
    product_id: int,
    quantity: int,
    priority: ProcurementPriority,
    reason: str,
) -> ProcurementRequest:
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

    req = ProcurementRequest(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        priority=priority,
        reason=reason,
        status=ProcurementStatus.PENDING_PROCUREMENT,
        created_at=datetime.now(timezone.utc),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_procurement_request(db: Session, request_id: int) -> ProcurementRequest | None:
    return db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()


def list_procurement_requests(db: Session) -> list[ProcurementRequest]:
    return db.query(ProcurementRequest).order_by(ProcurementRequest.created_at.desc()).all()


def approve_procurement_request(
    db: Session, request_id: int, acting_user: User
) -> ProcurementRequest:
    """Only MANAGER role may approve."""
    if acting_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only a MANAGER can approve procurement requests.")

    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail="Procurement request not found.")
    if req.status != ProcurementStatus.PENDING_PROCUREMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Request is already {req.status.value}, cannot approve.",
        )

    req.status = ProcurementStatus.APPROVED
    db.commit()
    db.refresh(req)
    return req


def reject_procurement_request(
    db: Session, request_id: int, acting_user: User
) -> ProcurementRequest:
    """Only MANAGER role may reject."""
    if acting_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only a MANAGER can reject procurement requests.")

    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail="Procurement request not found.")
    if req.status != ProcurementStatus.PENDING_PROCUREMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Request is already {req.status.value}, cannot reject.",
        )

    req.status = ProcurementStatus.REJECTED
    db.commit()
    db.refresh(req)
    return req


def cancel_procurement_request(
    db: Session, request_id: int, acting_user: User
) -> ProcurementRequest:
    """
    The request creator or a MANAGER may cancel a PENDING_PROCUREMENT request.
    Approved/Rejected requests cannot be cancelled.
    """
    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail="Procurement request not found.")

    # Authorization: creator or manager
    if acting_user.id != req.user_id and acting_user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only the request creator or a MANAGER can cancel a procurement request.",
        )

    if req.status != ProcurementStatus.PENDING_PROCUREMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Request is already {req.status.value}, cannot cancel.",
        )

    req.status = ProcurementStatus.CANCELLED
    db.commit()
    db.refresh(req)
    return req
