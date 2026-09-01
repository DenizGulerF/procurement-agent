"""Warehouse service."""

from sqlalchemy.orm import Session

from app.models.models import Warehouse, WarehouseLocation


def list_warehouses(db: Session) -> list[Warehouse]:
    return db.query(Warehouse).all()


def get_warehouse_locations(db: Session, warehouse_id: int) -> list[WarehouseLocation]:
    return (
        db.query(WarehouseLocation)
        .filter(WarehouseLocation.warehouse_id == warehouse_id)
        .all()
    )
