"""Tests — agent tools (called without LLM)."""

from app.agent.tools import execute_tool
from app.models.models import ProcurementStatus


def test_tool_search_product(seeded_db):
    result = execute_tool("search_product", {"query": "SKF"}, seeded_db, acting_user_id=1)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["sku"] == "SKF-6205"


def test_tool_check_stock(seeded_db):
    result = execute_tool("check_stock", {"product_id": 1}, seeded_db, acting_user_id=1)
    assert result["total_quantity"] == 23


def test_tool_find_product_locations(seeded_db):
    result = execute_tool("find_product_locations", {"product_id": 1}, seeded_db, acting_user_id=1)
    assert len(result) == 2
    assert sum(loc["quantity"] for loc in result) == 23


def test_tool_create_procurement_request(seeded_db):
    result = execute_tool(
        "create_procurement_request",
        {
            "user_id": 1,
            "product_id": 1,
            "quantity": 27,
            "priority": "HIGH",
            "reason": "Shortage after stock check",
        },
        seeded_db,
        acting_user_id=1,
    )
    assert "request_id" in result
    assert result["status"] == ProcurementStatus.PENDING_PROCUREMENT.value
    assert result["quantity"] == 27


def test_tool_get_user(seeded_db):
    result = execute_tool("get_user", {"user_id": 1}, seeded_db)
    assert result["name"] == "Ahmet"
    assert result["role"] == "EMPLOYEE"


def test_tool_unknown_tool(seeded_db):
    result = execute_tool("nonexistent_tool", {}, seeded_db)
    assert "error" in result


def test_tool_shortage_detection(seeded_db):
    """Verify the classic 50 requested / 23 available / 27 shortage scenario."""
    requested = 50
    stock_result = execute_tool("check_stock", {"product_id": 1}, seeded_db, acting_user_id=1)
    available = stock_result["total_quantity"]
    shortage = max(requested - available, 0)
    assert available == 23
    assert shortage == 27

    # Create a request for the shortage
    proc_result = execute_tool(
        "create_procurement_request",
        {
            "user_id": 1,
            "product_id": 1,
            "quantity": shortage,
            "priority": "HIGH",
            "reason": "Urgent — shortage detected",
        },
        seeded_db,
        acting_user_id=1,
    )
    assert proc_result["quantity"] == 27
    assert proc_result["status"] == "PENDING_PROCUREMENT"


def test_tool_audit_log_written(seeded_db):
    """Verify that tool calls produce audit logs."""
    from app.models.models import AuditLog

    before = seeded_db.query(AuditLog).count()
    execute_tool("check_stock", {"product_id": 1}, seeded_db, acting_user_id=1)
    after = seeded_db.query(AuditLog).count()
    assert after == before + 1
