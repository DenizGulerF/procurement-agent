"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.models import UserRole, ProcurementStatus, ProcurementPriority


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    name: str
    department: str
    role: UserRole

    model_config = {"from_attributes": True}


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str = "piece"
    description: str | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: str | None
    unit: str

    model_config = {"from_attributes": True}


# ── Warehouse / Location ──────────────────────────────────────────────────────

class WarehouseOut(BaseModel):
    id: int
    name: str
    location: str | None

    model_config = {"from_attributes": True}


class WarehouseLocationOut(BaseModel):
    id: int
    warehouse_id: int
    section: str
    shelf: str
    bin: str

    model_config = {"from_attributes": True}


# ── Inventory ─────────────────────────────────────────────────────────────────

class StockOut(BaseModel):
    product_id: int
    total_quantity: int


class LocationStockOut(BaseModel):
    inventory_id: int
    warehouse_id: int
    warehouse_name: str
    section: str
    shelf: str
    bin: str
    quantity: int


# ── Procurement ───────────────────────────────────────────────────────────────

class ProcurementRequestOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    priority: ProcurementPriority
    reason: str | None
    status: ProcurementStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    request_id: int | None
    tool_name: str
    arguments: Any
    result: Any
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    user_id: int
    message: str


class AgentResponse(BaseModel):
    response: str
    tool_calls: list[str] = []
