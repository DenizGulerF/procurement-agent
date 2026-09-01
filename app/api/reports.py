from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import LowStockItem, TopRequestedItem, PendingSummaryItem
from app.services import report_service, inventory_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/low-stock", response_model=list[LowStockItem])
def low_stock(db: Session = Depends(get_db)):
    """Products whose current stock is below their min_stock threshold."""
    return inventory_service.get_low_stock_items(db)


@router.get("/top-requested", response_model=list[TopRequestedItem])
def top_requested(
    days: int = Query(default=30, ge=1, le=365, description="Look-back window in days"),
    db: Session = Depends(get_db),
):
    """Top 10 most requested products in the last N days."""
    return report_service.get_top_requested(db, days=days)


@router.get("/pending-summary", response_model=list[PendingSummaryItem])
def pending_summary(db: Session = Depends(get_db)):
    """Products with open PENDING_PROCUREMENT requests, grouped by product."""
    return report_service.get_pending_summary(db)
