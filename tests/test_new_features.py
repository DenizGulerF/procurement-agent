"""Tests — create_product and cancel_procurement_request."""

import pytest
from fastapi import HTTPException

from app.services.product_service import create_product, search_product
from app.services.procurement_service import (
    create_procurement_request,
    cancel_procurement_request,
)
from app.services.user_service import get_user
from app.models.models import ProcurementStatus, ProcurementPriority
from app.agent.tools import execute_tool


# ── create_product ─────────────────────────────────────────────────────────────

def test_create_product_new(seeded_db):
    product = create_product(seeded_db, sku="SIEM-S7-1200", name="Siemens S7-1200 PLC", unit="piece")
    assert product.id is not None
    assert product.sku == "SIEM-S7-1200"
    assert product.name == "Siemens S7-1200 PLC"


def test_create_product_sku_normalized_to_uppercase(seeded_db):
    product = create_product(seeded_db, sku="test-sku-01", name="Test Product", unit="kg")
    assert product.sku == "TEST-SKU-01"


def test_create_product_duplicate_sku_raises(seeded_db):
    create_product(seeded_db, sku="UNIQUE-001", name="First", unit="piece")
    with pytest.raises(HTTPException) as exc_info:
        create_product(seeded_db, sku="UNIQUE-001", name="Duplicate", unit="piece")
    assert exc_info.value.status_code == 409


def test_create_product_searchable_after_creation(seeded_db):
    create_product(seeded_db, sku="BOSCH-GBH-36", name="Bosch GBH 36V Drill", unit="piece")
    results = search_product(seeded_db, "Bosch")
    assert len(results) == 1
    assert results[0].sku == "BOSCH-GBH-36"


def test_tool_create_product(seeded_db):
    result = execute_tool(
        "create_product",
        {"sku": "NEW-PART-99", "name": "New Part", "unit": "piece", "description": "Test part"},
        seeded_db,
        acting_user_id=1,
    )
    assert "product_id" in result
    assert result["sku"] == "NEW-PART-99"


def test_tool_create_product_then_procurement(seeded_db):
    """Full flow: create unknown product → open procurement request."""
    # Create product
    r1 = execute_tool(
        "create_product",
        {"sku": "FLOW-TEST-01", "name": "Flow Test Product", "unit": "piece"},
        seeded_db,
        acting_user_id=1,
    )
    assert "product_id" in r1

    # Open procurement for it
    r2 = execute_tool(
        "create_procurement_request",
        {
            "user_id": 1,
            "product_id": r1["product_id"],
            "quantity": 10,
            "priority": "NORMAL",
            "reason": "First purchase of this item",
        },
        seeded_db,
        acting_user_id=1,
    )
    assert r2["status"] == "PENDING_PROCUREMENT"
    assert r2["quantity"] == 10


# ── cancel_procurement_request ─────────────────────────────────────────────────

def test_creator_can_cancel_own_request(seeded_db):
    req = create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    acting = get_user(seeded_db, 1)  # Ahmet — creator
    cancelled = cancel_procurement_request(seeded_db, req.id, acting)
    assert cancelled.status == ProcurementStatus.CANCELLED


def test_manager_can_cancel_any_request(seeded_db):
    req = create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    manager = get_user(seeded_db, 3)  # Mehmet — MANAGER
    cancelled = cancel_procurement_request(seeded_db, req.id, manager)
    assert cancelled.status == ProcurementStatus.CANCELLED


def test_other_user_cannot_cancel_someone_elses_request(seeded_db):
    req = create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    other = get_user(seeded_db, 2)  # Ayse — PROCUREMENT, not the creator
    with pytest.raises(HTTPException) as exc_info:
        cancel_procurement_request(seeded_db, req.id, other)
    assert exc_info.value.status_code == 403


def test_cannot_cancel_approved_request(seeded_db):
    from app.services.procurement_service import approve_procurement_request
    req = create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    manager = get_user(seeded_db, 3)
    approve_procurement_request(seeded_db, req.id, manager)
    with pytest.raises(HTTPException) as exc_info:
        cancel_procurement_request(seeded_db, req.id, manager)
    assert exc_info.value.status_code == 400


def test_tool_cancel_procurement_request(seeded_db):
    req = create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    result = execute_tool(
        "cancel_procurement_request",
        {"request_id": req.id, "user_id": 1},
        seeded_db,
        acting_user_id=1,
    )
    assert result["status"] == "CANCELLED"
