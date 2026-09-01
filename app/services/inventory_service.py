"""Inventory service — stock checks and location lookups."""

from sqlalchemy.orm import Session, joinedload

from app.models.models import Inventory, WarehouseLocation, Warehouse


def check_stock(db: Session, product_id: int) -> dict:
    """Return total available quantity for a product across all locations."""
    rows = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .all()
    )
    total = sum(r.quantity for r in rows)
    return {"product_id": product_id, "total_quantity": total}


def find_product_locations(db: Session, product_id: int) -> list[dict]:
    """Return all locations where a product is stocked with quantities."""
    rows = (
        db.query(Inventory)
        .options(
            joinedload(Inventory.warehouse_location)
            .joinedload(WarehouseLocation.warehouse)
        )
        .filter(Inventory.product_id == product_id, Inventory.quantity > 0)
        .all()
    )
    result = []
    for row in rows:
        loc = row.warehouse_location
        wh = loc.warehouse
        result.append(
            {
                "inventory_id": row.id,
                "warehouse_id": wh.id,
                "warehouse_name": wh.name,
                "section": loc.section,
                "shelf": loc.shelf,
                "bin": loc.bin,
                "quantity": row.quantity,
            }
        )
    return result
