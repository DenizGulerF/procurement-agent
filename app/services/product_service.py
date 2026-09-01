"""Product service — search, lookup and creation."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

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


def create_product(
    db: Session,
    sku: str,
    name: str,
    unit: str,
    description: str | None = None,
) -> Product:
    """Create a new product. Raises 409 if SKU already exists."""
    existing = db.query(Product).filter(Product.sku == sku.strip().upper()).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A product with SKU '{sku}' already exists (id={existing.id}).",
        )
    product = Product(
        sku=sku.strip().upper(),
        name=name.strip(),
        unit=unit.strip(),
        description=description,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
