from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import WarehouseOut, WarehouseLocationOut
from app.services import warehouse_service

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return warehouse_service.list_warehouses(db)


@router.get("/{warehouse_id}/locations", response_model=list[WarehouseLocationOut])
def get_locations(warehouse_id: int, db: Session = Depends(get_db)):
    locations = warehouse_service.get_warehouse_locations(db, warehouse_id)
    if not locations:
        raise HTTPException(status_code=404, detail="Warehouse not found or has no locations.")
    return locations
