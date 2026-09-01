"""Tests — product search and stock/location lookups."""

from app.services.product_service import search_product, get_product
from app.services.inventory_service import check_stock, find_product_locations


def test_search_product_by_sku(seeded_db):
    results = search_product(seeded_db, "SKF-6205")
    assert len(results) == 1
    assert results[0].sku == "SKF-6205"


def test_search_product_by_name(seeded_db):
    results = search_product(seeded_db, "bearing")
    assert len(results) == 1
    assert results[0].name == "SKF 6205 Bearing"


def test_search_product_no_match(seeded_db):
    results = search_product(seeded_db, "nonexistent_xyz")
    assert results == []


def test_get_product_found(seeded_db):
    product = get_product(seeded_db, 1)
    assert product is not None
    assert product.sku == "SKF-6205"


def test_get_product_not_found(seeded_db):
    product = get_product(seeded_db, 9999)
    assert product is None


def test_check_stock_total(seeded_db):
    stock = check_stock(seeded_db, 1)
    assert stock["product_id"] == 1
    assert stock["total_quantity"] == 23  # 15 + 8


def test_check_stock_zero_for_unknown(seeded_db):
    stock = check_stock(seeded_db, 9999)
    assert stock["total_quantity"] == 0


def test_find_product_locations(seeded_db):
    locations = find_product_locations(seeded_db, 1)
    assert len(locations) == 2
    total = sum(loc["quantity"] for loc in locations)
    assert total == 23
    warehouse_names = {loc["warehouse_name"] for loc in locations}
    assert "Warehouse A" in warehouse_names
