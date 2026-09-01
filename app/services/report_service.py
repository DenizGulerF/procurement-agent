"""Report service — aggregated views for management."""

from datetime import datetime, timezone, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import ProcurementRequest, ProcurementStatus, Product


def get_top_requested(db: Session, days: int = 30) -> list[dict]:
    """Products with the most total requested quantity in the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(
            Product.id,
            Product.sku,
            Product.name,
            func.sum(ProcurementRequest.quantity).label("total_requested"),
            func.count(ProcurementRequest.id).label("request_count"),
        )
        .join(ProcurementRequest, ProcurementRequest.product_id == Product.id)
        .filter(ProcurementRequest.created_at >= since)
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(ProcurementRequest.quantity).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "product_id": r.id,
            "sku": r.sku,
            "name": r.name,
            "total_requested": r.total_requested,
            "request_count": r.request_count,
        }
        for r in rows
    ]


def get_pending_summary(db: Session) -> list[dict]:
    """Products with PENDING_PROCUREMENT requests, grouped by product."""
    rows = (
        db.query(
            Product.id,
            Product.sku,
            Product.name,
            func.sum(ProcurementRequest.quantity).label("pending_quantity"),
            func.count(ProcurementRequest.id).label("request_count"),
        )
        .join(ProcurementRequest, ProcurementRequest.product_id == Product.id)
        .filter(ProcurementRequest.status == ProcurementStatus.PENDING_PROCUREMENT)
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(ProcurementRequest.quantity).desc())
        .all()
    )

    return [
        {
            "product_id": r.id,
            "sku": r.sku,
            "name": r.name,
            "pending_quantity": r.pending_quantity,
            "request_count": r.request_count,
        }
        for r in rows
    ]
