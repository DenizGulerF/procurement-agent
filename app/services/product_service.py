"""Product service — search and lookup."""

from sqlalchemy.orm import Session

from app.models.models import Product


def search_product(db: Session, query: str) -> list[Product]:
    """Search products by name or SKU (case-insensitive substring)."""
    q = f"%{query.strip()}%"
    return (
        db.query(Product)
        .filter(
            (Product.name.ilike(q)) | (Product.sku.ilike(q))
        )
        .all()
    )


def get_product(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def list_products(db: Session) -> list[Product]:
    return db.query(Product).all()
