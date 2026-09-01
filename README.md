# ProcureAI

An AI-powered procurement and warehouse assistant demonstrating how an LLM can safely operate real business workflows through **controlled tools**, **application-level authorization**, and **human approval**.

> **Tested with a local LLM** — [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (Q5_K_M, GGUF) running on [llama.cpp](https://github.com/ggerganov/llama.cpp) server. Works with any OpenAI-compatible server (Ollama, LM Studio, etc.) as well as the OpenAI cloud API.

---

## What is ProcureAI?

ProcureAI accepts natural-language requests from users and routes them through a controlled set of business tools. The AI agent can search products, check inventory, locate stock in warehouses, and create procurement requests — but it cannot approve requests, alter stock, or execute arbitrary database queries. All critical decisions remain in application code or with human approvers.

---

## Architecture

```
User (natural language)
        │
        ▼
   FastAPI /agent/request
        │
        ▼
   AI Agent (OpenAI-compatible tool-calling loop)
        │
   ┌────┴────────────────────┐
   │                         │
   ▼                         ▼
Business Tools          Application services
(get_user,              (product_service,
 search_product,         inventory_service,
 check_stock,            procurement_service,
 find_product_locations, audit_service)
 create_procurement_request,
 get_procurement_request)
        │
        ▼
   PostgreSQL (via SQLAlchemy)
        │
        ▼
   Audit Logs
```

---

## Agent / Tool Model

The LLM decides **which tool to call** and **in which order**. The application decides:

- whether the user is authorized
- stock calculations
- procurement status transitions
- approval permissions
- database writes

The model never generates or executes arbitrary SQL.

---

## LLM Backend

The agent uses the OpenAI Python client and works with **any OpenAI-compatible endpoint** — local or cloud. Configure via `.env`:

| Variable | Description |
|---|---|
| `LLM_BASE_URL` | Base URL of the LLM server. Empty = OpenAI cloud. |
| `LLM_MODEL` | Model name/ID sent to the server. |
| `OPENAI_API_KEY` | API key. Use `local` for local servers that don't require auth. |

### Tested setup — llama.cpp + Qwen3-8B

```env
LLM_BASE_URL=http://host.docker.internal:8082/v1
LLM_MODEL=C:\Users\...\models\qwen3-8b-q5_k_m.gguf
OPENAI_API_KEY=local
```

### Other local options

```env
# Ollama
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=qwen3

# LM Studio
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_MODEL=local-model
```

### OpenAI cloud

```env
LLM_BASE_URL=           # leave empty
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

---

## Warehouse & Inventory Features

- Products are identified by SKU and stored in one or more warehouse locations
- Each location has a warehouse, section, shelf, and bin address
- Stock is tracked per location; `check_stock` returns the total across all locations
- `find_product_locations` returns each location with its quantity

---

## Procurement Workflow

```
User request (natural language)
        │
        ▼
Agent: search_product → check_stock → calculate shortage
        │
        ▼
Agent: create_procurement_request  →  PENDING_PROCUREMENT
        │
        ▼
Human Manager: POST /procurement/requests/{id}/approve  →  APPROVED
                                               or reject  →  REJECTED
```

- The AI **cannot approve** its own requests
- Only users with the `MANAGER` role may approve or reject
- All tool calls are written to the audit log

---

## Authorization

| Role        | Can do                                        |
|-------------|-----------------------------------------------|
| EMPLOYEE    | Search products, check stock, create requests |
| WAREHOUSE   | Search products, check stock                  |
| PROCUREMENT | Search products, check stock, view requests   |
| MANAGER     | View, approve, reject requests                |

Authorization is enforced in application code — the LLM is never trusted for authorization decisions.

---

## Human-in-the-Loop

A procurement request created by the agent always starts as `PENDING_PROCUREMENT`. A human manager must call the approve or reject endpoint. The agent has no tool to approve requests.

---

## Auditability

Every agent tool call writes an `AuditLog` row containing:

- `user_id` — who triggered the action
- `tool_name` — which tool was called
- `arguments` — exact arguments (JSON)
- `result` — what the tool returned (JSON)
- `created_at` — timestamp
- `request_id` — linked to procurement request when relevant

---

## Docker Setup

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env — set LLM_BASE_URL + LLM_MODEL for local, or OPENAI_API_KEY for cloud

# 2. Start everything
docker compose up --build

# 3. Open API docs
open http://localhost:8000/docs
```

PostgreSQL starts automatically. Seed data is inserted on first startup.

---

## Demo Users (seed data)

| ID | Name   | Department  | Role        |
|----|--------|-------------|-------------|
| 1  | Ahmet  | Maintenance | EMPLOYEE    |
| 2  | Ayse   | Procurement | PROCUREMENT |
| 3  | Mehmet | Management  | MANAGER     |
| 4  | Ali    | Warehouse   | WAREHOUSE   |

---

## Demo Products (seed data)

| SKU      | Name             | Stock |
|----------|------------------|-------|
| SKF-6205 | SKF 6205 Bearing | 23 (split across 2 locations — insufficient for 50) |
| A4-80GSM | A4 Paper 80gsm   | 200   |
| M12-BOLT | M12 Bolt DIN 933 | 500   |

---

## Example API Usage

### Agent natural-language request

```http
POST /agent/request
Content-Type: application/json

{
  "user_id": 1,
  "message": "We need 50 SKF 6205 bearings urgently for maintenance. Check whether we have enough in stock and create a procurement request for anything missing."
}
```

Expected agent flow:
```
search_product("SKF 6205")  →  product_id=1
check_stock(1)              →  total=23
shortage = 50 - 23 = 27
create_procurement_request(user_id=1, product_id=1, quantity=27, priority="HIGH", ...)
→ PENDING_PROCUREMENT (request_id=N)
```

### Approve as manager

```http
POST /procurement/requests/{id}/approve?acting_user_id=3
```

### Read audit log

```http
GET /audit/{request_id}
```

---

## Example Agent Conversation

Tested with **Qwen3-8B Q5_K_M** via llama.cpp:

**Input:**
> "We need 50 SKF 6205 bearings urgently for maintenance. Check stock and create a procurement request for anything missing."

**Agent tool calls:** `search_product → check_stock → create_procurement_request`

**Agent output:**
> A procurement request has been created for **27 SKF 6205 bearings** (request ID: 1). The request is pending approval and will be prioritized urgently for maintenance.

**Location query** — Input:
> "Where exactly can I find the SKF 6205 bearings in the warehouse?"

**Agent tool calls:** `search_product → find_product_locations`

**Agent output:**
> The SKF 6205 bearings are located in:
> - **Warehouse A** — Section B / Shelf 14 / Bin 02 — 15 pieces
> - **Warehouse B** — Section A / Shelf 07 / Bin 04 — 8 pieces

---

## Running Tests

```bash
docker compose exec app python -m pytest tests/ -v
```

All 31 tests cover:
- Product search and stock lookup
- Location lookup
- Shortage detection
- Procurement creation and retrieval
- Authorization (employee cannot approve, manager can)
- Procurement status transitions (PENDING → APPROVED / REJECTED)
- Audit log creation on tool invocation
- HTTP API endpoints

---

## Project Structure

```
app/
├── main.py              # FastAPI app, startup, router registration
├── config.py            # Environment settings (LLM_BASE_URL, LLM_MODEL, etc.)
├── auth.py              # Role-based authorization helpers
├── api/
│   ├── agent.py         # POST /agent/request
│   ├── products.py      # GET /products, /products/{id}
│   ├── inventory.py     # GET /inventory/{product_id}
│   ├── warehouse.py     # GET /warehouses, /warehouses/{id}/locations
│   ├── procurement.py   # GET/POST /procurement/requests/...
│   └── audit.py         # GET /audit/{request_id}
├── agent/
│   ├── service.py       # LLM tool-calling loop (OpenAI-compatible)
│   ├── tools.py         # Tool definitions + execution dispatcher
│   └── prompts.py       # System prompt
├── models/
│   └── models.py        # SQLAlchemy ORM models
├── schemas/
│   └── schemas.py       # Pydantic request/response schemas
├── services/
│   ├── product_service.py
│   ├── inventory_service.py
│   ├── procurement_service.py
│   ├── audit_service.py
│   ├── user_service.py
│   └── warehouse_service.py
└── db/
    ├── session.py       # SQLAlchemy engine + session
    └── seed.py          # Deterministic demo data

tests/
├── conftest.py          # SQLite in-memory test fixtures
├── test_inventory.py    # Product search, stock, locations
├── test_procurement.py  # Procurement workflow + auth
├── test_tools.py        # Agent tools (without LLM)
└── test_api.py          # HTTP endpoint tests
```

---

## Future Extensions

- React / Next.js frontend
- JWT authentication
- Multi-tenant support
- Celery + Redis for async agent jobs
- WhatsApp / Slack notification on approval
- Real ERP integration (SAP, Oracle)
- MCP server for richer tool ecosystem
- RAG over product catalog / manuals
