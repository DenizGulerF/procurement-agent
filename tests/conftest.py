"""
Shared pytest fixtures — in-memory SQLite test database.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.session import Base, get_db
from app.main import app
from app.models.models import (
    User, Product, Warehouse, WarehouseLocation, Inventory,
    UserRole,
)

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # all connections share the same in-memory db
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seeded_client(seeded_db):
    """TestClient wired to the already-seeded SQLite database."""
    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seeded_db(db):
    """Return a db session populated with minimal test data."""
    # Users
    employee = User(id=1, name="Ahmet", department="Maintenance", role=UserRole.EMPLOYEE)
    procurement = User(id=2, name="Ayse", department="Procurement", role=UserRole.PROCUREMENT)
    manager = User(id=3, name="Mehmet", department="Management", role=UserRole.MANAGER)
    warehouse_user = User(id=4, name="Ali", department="Warehouse", role=UserRole.WAREHOUSE)
    db.add_all([employee, procurement, manager, warehouse_user])

    # Products
    bearing = Product(id=1, sku="SKF-6205", name="SKF 6205 Bearing", unit="piece")
    paper = Product(id=2, sku="A4-80GSM", name="A4 Paper", unit="ream")
    db.add_all([bearing, paper])

    # Warehouses + Locations
    wh_a = Warehouse(id=1, name="Warehouse A", location="Sector 1")
    db.add(wh_a)
    db.flush()
    loc1 = WarehouseLocation(id=1, warehouse_id=1, section="B", shelf="Shelf 14", bin="Bin 02")
    loc2 = WarehouseLocation(id=2, warehouse_id=1, section="C", shelf="Shelf 03", bin="Bin 11")
    db.add_all([loc1, loc2])
    db.flush()

    # Inventory: bearing=23 (insufficient for 50), paper=200
    db.add(Inventory(product_id=1, warehouse_location_id=1, quantity=15))
    db.add(Inventory(product_id=1, warehouse_location_id=2, quantity=8))
    db.add(Inventory(product_id=2, warehouse_location_id=2, quantity=200))
    db.commit()
    return db
