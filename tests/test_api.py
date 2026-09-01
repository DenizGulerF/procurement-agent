"""Tests — HTTP API endpoints."""

from app.models.models import ProcurementStatus


def test_health(seeded_client):
    resp = seeded_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_products(seeded_client):
    resp = seeded_client.get("/products")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_get_product_found(seeded_client):
    resp = seeded_client.get("/products/1")
    assert resp.status_code == 200
    assert resp.json()["sku"] == "SKF-6205"


def test_get_product_not_found(seeded_client):
    resp = seeded_client.get("/products/9999")
    assert resp.status_code == 404


def test_inventory_stock(seeded_client):
    resp = seeded_client.get("/inventory/1")
    assert resp.status_code == 200
    assert resp.json()["total_quantity"] == 23


def test_inventory_locations(seeded_client):
    resp = seeded_client.get("/inventory/1/locations")
    assert resp.status_code == 200
    locations = resp.json()
    assert len(locations) == 2


def test_list_warehouses(seeded_client):
    resp = seeded_client.get("/warehouses")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_procurement_workflow_via_api(seeded_client, seeded_db):
    """EMPLOYEE cannot approve; MANAGER can."""
    from app.services.procurement_service import create_procurement_request
    from app.models.models import ProcurementPriority

    req = create_procurement_request(
        db=seeded_db,
        user_id=1,
        product_id=1,
        quantity=10,
        priority=ProcurementPriority.NORMAL,
        reason="test",
    )

    # EMPLOYEE (user 1) tries to approve — should fail
    resp = seeded_client.post(f"/procurement/requests/{req.id}/approve?acting_user_id=1")
    assert resp.status_code == 403

    # MANAGER (user 3) approves — should succeed
    resp = seeded_client.post(f"/procurement/requests/{req.id}/approve?acting_user_id=3")
    assert resp.status_code == 200
    assert resp.json()["status"] == ProcurementStatus.APPROVED.value
