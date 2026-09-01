"""
Seed script — populates the database with deterministic demo data.

Run inside the app container:
    python -m app.db.seed

Or via docker:
    docker compose exec app python -m app.db.seed
"""

from app.db.session import SessionLocal
from app.models.models import (
    User, Product, Warehouse, WarehouseLocation, Inventory,
    UserRole,
)


def seed():
    db = SessionLocal()
    try:
        # Idempotent: skip if data already exists
        if db.query(User).count() > 0:
            print("Seed data already present, skipping.")
            return

        # ── Users ──────────────────────────────────────────────────────────
        users = [
            User(id=1, name="Ahmet", department="Maintenance", role=UserRole.EMPLOYEE),
            User(id=2, name="Ayse", department="Procurement", role=UserRole.PROCUREMENT),
            User(id=3, name="Mehmet", department="Management", role=UserRole.MANAGER),
            User(id=4, name="Ali", department="Warehouse", role=UserRole.WAREHOUSE),
        ]
        db.add_all(users)
        db.flush()

        # ── Products ───────────────────────────────────────────────────────
        products = [
            Product(
                id=1,
                sku="SKF-6205",
                name="SKF 6205 Bearing",
                description="Deep groove ball bearing 25x52x15mm",
                unit="piece",
                min_stock=30,   # stok 23 < 30 → low-stock demo
            ),
            Product(
                id=2,
                sku="A4-80GSM",
                name="A4 Paper 80gsm",
                description="Standard copy paper, 500 sheets per ream",
                unit="ream",
                min_stock=50,   # stok 200 > 50 → yeterli
            ),
            Product(
                id=3,
                sku="M12-BOLT",
                name="M12 Bolt DIN 933",
                description="Stainless steel hex bolt M12x50",
                unit="piece",
                min_stock=100,  # stok 500 > 100 → yeterli
            ),
        ]
        db.add_all(products)
        db.flush()

        # ── Warehouses ─────────────────────────────────────────────────────
        warehouses = [
            Warehouse(id=1, name="Warehouse A", location="Istanbul, Sector 1"),
            Warehouse(id=2, name="Warehouse B", location="Istanbul, Sector 2"),
        ]
        db.add_all(warehouses)
        db.flush()

        # ── Warehouse Locations ────────────────────────────────────────────
        # Warehouse A
        loc1 = WarehouseLocation(id=1, warehouse_id=1, section="B", shelf="Shelf 14", bin="Bin 02")
        loc2 = WarehouseLocation(id=2, warehouse_id=1, section="C", shelf="Shelf 03", bin="Bin 11")
        # Warehouse B
        loc3 = WarehouseLocation(id=3, warehouse_id=2, section="A", shelf="Shelf 07", bin="Bin 04")
        loc4 = WarehouseLocation(id=4, warehouse_id=2, section="D", shelf="Shelf 01", bin="Bin 09")

        db.add_all([loc1, loc2, loc3, loc4])
        db.flush()

        # ── Inventory ──────────────────────────────────────────────────────
        # SKF 6205 Bearing: split across two locations (total 23 — insufficient for 50 demo)
        inv = [
            Inventory(product_id=1, warehouse_location_id=1, quantity=15),  # WH-A / B / S14 / B02
            Inventory(product_id=1, warehouse_location_id=3, quantity=8),   # WH-B / A / S07 / B04
            # A4 Paper: single location, more than enough
            Inventory(product_id=2, warehouse_location_id=2, quantity=200),  # WH-A / C / S03 / B11
            # M12 Bolt: single location, sufficient stock
            Inventory(product_id=3, warehouse_location_id=4, quantity=500),  # WH-B / D / S01 / B09
        ]
        db.add_all(inv)

        db.commit()
        print("Seed data inserted successfully.")
        print("  Users: 4")
        print("  Products: 3 (SKF-6205, A4-80GSM, M12-BOLT)")
        print("  Warehouses: 2")
        print("  Locations: 4")
        print("  Inventory: SKF-6205=23 total (15+8), A4-80GSM=200, M12-BOLT=500")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
