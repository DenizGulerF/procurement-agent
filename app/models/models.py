import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum as SAEnum, JSON, func
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    WAREHOUSE = "WAREHOUSE"
    PROCUREMENT = "PROCUREMENT"
    MANAGER = "MANAGER"


class ProcurementStatus(str, enum.Enum):
    PENDING_PROCUREMENT = "PENDING_PROCUREMENT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ProcurementPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)

    procurement_requests = relationship("ProcurementRequest", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=False, default="piece")
    min_stock = Column(Integer, nullable=False, default=0)

    inventory = relationship("Inventory", back_populates="product")
    procurement_requests = relationship("ProcurementRequest", back_populates="product")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(300), nullable=True)

    warehouse_locations = relationship("WarehouseLocation", back_populates="warehouse")


class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    section = Column(String(50), nullable=False)
    shelf = Column(String(50), nullable=False)
    bin = Column(String(50), nullable=False)

    warehouse = relationship("Warehouse", back_populates="warehouse_locations")
    inventory = relationship("Inventory", back_populates="warehouse_location")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_location_id = Column(Integer, ForeignKey("warehouse_locations.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="inventory")
    warehouse_location = relationship("WarehouseLocation", back_populates="inventory")


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(SAEnum(ProcurementPriority), nullable=False, default=ProcurementPriority.NORMAL)
    reason = Column(Text, nullable=True)
    status = Column(
        SAEnum(ProcurementStatus),
        nullable=False,
        default=ProcurementStatus.PENDING_PROCUREMENT,
    )
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    user = relationship("User", back_populates="procurement_requests")
    product = relationship("Product", back_populates="procurement_requests")
    audit_logs = relationship("AuditLog", back_populates="procurement_request")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_id = Column(Integer, ForeignKey("procurement_requests.id"), nullable=True)
    tool_name = Column(String(200), nullable=False)
    arguments = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
    procurement_request = relationship("ProcurementRequest", back_populates="audit_logs")
