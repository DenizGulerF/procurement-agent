"""Tests — reorder point and reporting."""

from app.services.inventory_service import get_low_stock_items
from app.services.report_service import get_top_requested, get_pending_summary
from app.services.procurement_service import create_procurement_request, approve_procurement_request
from app.services.user_service import get_user
from app.models.models import ProcurementPriority
from app.agent.tools import execute_tool


# ── Reorder point ─────────────────────────────────────────────────────────────

def test_low_stock_returns_items_below_threshold(seeded_db):
    # SKF-6205: stock=23, min_stock=30 → should appear
    items = get_low_stock_items(seeded_db)
    skus = [i["sku"] for i in items]
    assert "SKF-6205" in skus


def test_low_stock_excludes_sufficient_items(seeded_db):
    # A4-80GSM: stock=200, min_stock=50 → should NOT appear
    # M12-BOLT: stock=500, min_stock=100 → should NOT appear
    items = get_low_stock_items(seeded_db)
    skus = [i["sku"] for i in items]
    assert "A4-80GSM" not in skus
    assert "M12-BOLT" not in skus


def test_low_stock_item_has_correct_shortage(seeded_db):
    items = get_low_stock_items(seeded_db)
    skf = next(i for i in items if i["sku"] == "SKF-6205")
    assert skf["current_stock"] == 23
    assert skf["min_stock"] == 30
    assert skf["shortage"] == 7


def test_tool_find_low_stock_items(seeded_db):
    result = execute_tool("find_low_stock_items", {}, seeded_db, acting_user_id=1)
    assert isinstance(result, list)
    skus = [i["sku"] for i in result]
    assert "SKF-6205" in skus


def test_product_without_min_stock_not_in_low_stock(seeded_db):
    # Create a product with min_stock=0 (default)
    from app.services.product_service import create_product
    create_product(seeded_db, sku="NO-MIN-001", name="No Min Stock Product", unit="piece", min_stock=0)
    items = get_low_stock_items(seeded_db)
    skus = [i["sku"] for i in items]
    assert "NO-MIN-001" not in skus


# ── Reporting ─────────────────────────────────────────────────────────────────

def test_top_requested_returns_most_requested(seeded_db):
    # Create some requests
    create_procurement_request(seeded_db, 1, 1, 50, ProcurementPriority.HIGH, "test1")
    create_procurement_request(seeded_db, 1, 1, 30, ProcurementPriority.NORMAL, "test2")
    create_procurement_request(seeded_db, 1, 2, 10, ProcurementPriority.LOW, "test3")

    results = get_top_requested(seeded_db, days=30)
    assert len(results) >= 1
    # SKF-6205 has 80 total requested → should be first
    assert results[0]["sku"] == "SKF-6205"
    assert results[0]["total_requested"] == 80
    assert results[0]["request_count"] == 2


def test_pending_summary_shows_only_pending(seeded_db):
    req1 = create_procurement_request(seeded_db, 1, 1, 27, ProcurementPriority.HIGH, "pending")
    req2 = create_procurement_request(seeded_db, 1, 1, 10, ProcurementPriority.NORMAL, "will approve")
    manager = get_user(seeded_db, 3)
    approve_procurement_request(seeded_db, req2.id, manager)

    results = get_pending_summary(seeded_db)
    assert len(results) >= 1
    skf = next((r for r in results if r["sku"] == "SKF-6205"), None)
    assert skf is not None
    # Only req1 is pending, req2 is approved
    assert skf["pending_quantity"] == 27
    assert skf["request_count"] == 1


def test_tool_get_report_top_requested(seeded_db):
    create_procurement_request(seeded_db, 1, 1, 20, ProcurementPriority.NORMAL, "test")
    result = execute_tool(
        "get_report",
        {"report_type": "top_requested", "days": 30},
        seeded_db,
        acting_user_id=1,
    )
    assert isinstance(result, list)


def test_tool_get_report_pending_summary(seeded_db):
    create_procurement_request(seeded_db, 1, 1, 5, ProcurementPriority.LOW, "test")
    result = execute_tool(
        "get_report",
        {"report_type": "pending_summary"},
        seeded_db,
        acting_user_id=1,
    )
    assert isinstance(result, list)
    assert len(result) >= 1


def test_tool_get_report_unknown_type(seeded_db):
    result = execute_tool("get_report", {"report_type": "nonexistent"}, seeded_db)
    assert "error" in result
