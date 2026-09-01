from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import StockOut, LocationStockOut
from app.services import inventory_service, product_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/{product_id}", response_model=StockOut)
def get_stock(product_id: int, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return inventory_service.check_stock(db, product_id)


@router.get("/{product_id}/locations", response_model=list[LocationStockOut])
def get_locations(product_id: int, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return inventory_service.find_product_locations(db, product_id)
