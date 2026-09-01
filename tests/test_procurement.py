"""Tests — procurement workflow and authorization."""
import pytest

from fastapi import HTTPException

from app.services.procurement_service import (
    create_procurement_request,
    get_procurement_request,
    approve_procurement_request,
    reject_procurement_request,
)
from app.services.user_service import get_user
from app.models.models import ProcurementStatus, ProcurementPriority


def test_create_procurement_request_pending(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=27,
        priority=ProcurementPriority.HIGH,
        reason="Urgent maintenance need",
    )
    assert req.id is not None
    assert req.status == ProcurementStatus.PENDING_PROCUREMENT
    assert req.quantity == 27


def test_create_procurement_request_invalid_quantity(seeded_db):
    with pytest.raises(ValueError, match="Quantity must be positive"):
        create_procurement_request(
            db=seeded_db,
            user_id=1,
            product_id=1,
            quantity=0,
            priority=ProcurementPriority.NORMAL,
            reason="test",
        )


def test_approved_request_becomes_approved(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=10,
        priority=ProcurementPriority.NORMAL,
        reason="test",
    )
    manager = get_user(seeded_db, 3)  # Mehmet - MANAGER
    approved = approve_procurement_request(seeded_db, req.id, manager)
    assert approved.status == ProcurementStatus.APPROVED


def test_rejected_request_becomes_rejected(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=10,
        priority=ProcurementPriority.NORMAL,
        reason="test",
    )
    manager = get_user(seeded_db, 3)  # MANAGER
    rejected = reject_procurement_request(seeded_db, req.id, manager)
    assert rejected.status == ProcurementStatus.REJECTED


def test_employee_cannot_approve(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=5,
        priority=ProcurementPriority.LOW,
        reason="test",
    )
    employee = get_user(seeded_db, 1)  # Ahmet - EMPLOYEE
    with pytest.raises(HTTPException) as exc_info:
        approve_procurement_request(seeded_db, req.id, employee)
    assert exc_info.value.status_code == 403


def test_manager_can_approve(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=5,
        priority=ProcurementPriority.NORMAL,
        reason="test",
    )
    manager = get_user(seeded_db, 3)
    result = approve_procurement_request(seeded_db, req.id, manager)
    assert result.status == ProcurementStatus.APPROVED


def test_get_procurement_request(seeded_db):
    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=5,
        priority=ProcurementPriority.NORMAL,
        reason="test",
    )
    fetched = get_procurement_request(seeded_db, req.id)
    assert fetched is not None
    assert fetched.id == req.id
    assert fetched.status == ProcurementStatus.PENDING_PROCUREMENT
