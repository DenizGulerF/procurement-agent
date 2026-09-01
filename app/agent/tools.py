"""
Agent tools — wrap business services as controlled LLM tools.

Each tool:
- validates inputs
- calls application services
- returns structured data
- writes an audit log

No duplicated business rules live here.
"""

from sqlalchemy.orm import Session

from app.services import (
    product_service,
    inventory_service,
    procurement_service,
    user_service,
    audit_service,
)
from app.models.models import ProcurementPriority
from app.auth import can_create_procurement


# ── OpenAI tool definitions (JSON schema) ─────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get details about a user by their ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "The user's ID."},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "Search for products by name or SKU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term — product name or SKU."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Get a product's details by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The product's ID."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Get the total available stock quantity for a product across all warehouse locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The product's ID."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_product_locations",
            "description": "Find all warehouse locations where a product is stocked, with quantity at each location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The product's ID."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_procurement_request",
            "description": (
                "Create a procurement request for a product when stock is insufficient. "
                "This creates a PENDING_PROCUREMENT request that requires human approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "ID of the user making the request."},
                    "product_id": {"type": "integer", "description": "ID of the product to procure."},
                    "quantity": {"type": "integer", "description": "Quantity to procure."},
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "NORMAL", "HIGH"],
                        "description": "Priority of the request.",
                    },
                    "reason": {"type": "string", "description": "Reason for the procurement request."},
                },
                "required": ["user_id", "product_id", "quantity", "priority", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_procurement_request",
            "description": "Get the status and details of a procurement request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer", "description": "The procurement request ID."},
                },
                "required": ["request_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_product",
            "description": (
                "Register a new product in the system. Use this when a product cannot be found "
                "by search_product and needs to be created before a procurement request can be opened."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Unique product SKU code (e.g. SIEM-S7-1200)."},
                    "name": {"type": "string", "description": "Full product name."},
                    "unit": {"type": "string", "description": "Unit of measure (piece, kg, litre, etc.)."},
                    "description": {"type": "string", "description": "Optional product description."},
                },
                "required": ["sku", "name", "unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_procurement_request",
            "description": "Cancel a PENDING_PROCUREMENT request. Only the request creator or a MANAGER may cancel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer", "description": "The procurement request ID to cancel."},
                    "user_id": {"type": "integer", "description": "ID of the user requesting the cancellation."},
                },
                "required": ["request_id", "user_id"],
            },
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────

def execute_tool(
    tool_name: str,
    arguments: dict,
    db: Session,
    acting_user_id: int | None = None,
) -> dict:
    """
    Dispatch a tool call to the appropriate service.
    Returns a dict that will be serialised and fed back to the LLM.
    """
    if tool_name == "get_user":
        user = user_service.get_user(db, arguments["user_id"])
        if not user:
            result = {"error": f"User {arguments['user_id']} not found."}
        else:
            result = {
                "id": user.id,
                "name": user.name,
                "department": user.department,
                "role": user.role.value,
            }

    elif tool_name == "search_product":
        products = product_service.search_product(db, arguments["query"])
        result = [
            {"id": p.id, "sku": p.sku, "name": p.name, "unit": p.unit}
            for p in products
        ]

    elif tool_name == "get_product":
        product = product_service.get_product(db, arguments["product_id"])
        if not product:
            result = {"error": f"Product {arguments['product_id']} not found."}
        else:
            result = {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "unit": product.unit,
            }

    elif tool_name == "check_stock":
        result = inventory_service.check_stock(db, arguments["product_id"])

    elif tool_name == "find_product_locations":
        result = inventory_service.find_product_locations(db, arguments["product_id"])

    elif tool_name == "create_procurement_request":
        # Authorization check
        user = user_service.get_user(db, arguments["user_id"])
        if not user:
            result = {"error": f"User {arguments['user_id']} not found."}
        elif not can_create_procurement(user):
            result = {"error": f"User role {user.role.value} is not authorized to create procurement requests."}
        else:
            try:
                priority = ProcurementPriority(arguments["priority"])
                req = procurement_service.create_procurement_request(
                    db=db,
                    user_id=arguments["user_id"],
                    product_id=arguments["product_id"],
                    quantity=arguments["quantity"],
                    priority=priority,
                    reason=arguments["reason"],
                )
                result = {
                    "request_id": req.id,
                    "status": req.status.value,
                    "product_id": req.product_id,
                    "quantity": req.quantity,
                    "priority": req.priority.value,
                    "reason": req.reason,
                    "created_at": req.created_at.isoformat(),
                }
            except ValueError as e:
                result = {"error": str(e)}

    elif tool_name == "get_procurement_request":
        req = procurement_service.get_procurement_request(db, arguments["request_id"])
        if not req:
            result = {"error": f"Procurement request {arguments['request_id']} not found."}
        else:
            result = {
                "request_id": req.id,
                "status": req.status.value,
                "product_id": req.product_id,
                "quantity": req.quantity,
                "priority": req.priority.value,
                "reason": req.reason,
                "created_at": req.created_at.isoformat(),
            }

    elif tool_name == "create_product":
        try:
            product = product_service.create_product(
                db=db,
                sku=arguments["sku"],
                name=arguments["name"],
                unit=arguments.get("unit", "piece"),
                description=arguments.get("description"),
            )
            result = {
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "unit": product.unit,
                "description": product.description,
            }
        except Exception as e:
            result = {"error": str(e)}

    elif tool_name == "cancel_procurement_request":
        user = user_service.get_user(db, arguments["user_id"])
        if not user:
            result = {"error": f"User {arguments['user_id']} not found."}
        else:
            try:
                req = procurement_service.cancel_procurement_request(
                    db=db,
                    request_id=arguments["request_id"],
                    acting_user=user,
                )
                result = {
                    "request_id": req.id,
                    "status": req.status.value,
                }
            except Exception as e:
                result = {"error": str(e)}

    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    # Write audit log for every tool call
    audit_service.write_audit_log(
        db=db,
        tool_name=tool_name,
        arguments=arguments,
        result=result if isinstance(result, dict) else {"items": result},
        user_id=acting_user_id,
    )

    return result
