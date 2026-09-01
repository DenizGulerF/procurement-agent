# ProcureAI — Implementation Plan

> **Purpose:** This document is the single source of truth for implementing the ProcureAI portfolio MVP.
>
> **Target:** Finish a clean, working demo in one day. Prioritize correctness, simplicity, and a clear agentic workflow over feature count.
>
> **Important:** Read this file completely before making changes. Follow the phases in order. Do not skip validation steps. Do not overengineer.

---

# 1. Project Goal

Build **ProcureAI**, an AI-powered procurement and warehouse assistant.

The user interacts with the system using natural language. The AI agent decides which controlled business tools to use to answer the request or advance a procurement workflow.

The agent must be able to:

- Search products.
- Check current stock.
- Find which warehouse contains a product.
- Find the physical location of stock inside a warehouse.
- Determine whether requested stock is sufficient.
- Calculate shortages.
- Create procurement requests when stock is insufficient.
- Read procurement request status.
- Respect application-level authorization.
- Never directly access the database through arbitrary SQL.
- Never bypass human approval for procurement decisions.
- Produce audit logs for important tool calls.

The central workflow is:

```text
User
  ↓
Natural-language request
  ↓
AI Agent
  ↓
Controlled business tools
  ↓
Warehouse / Inventory / Procurement
  ↓
Procurement request
  ↓
Human approval
  ↓
Auditable result
```

---

# 2. MVP Scope

## Must Have

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- OpenAI API with tool/function calling
- Docker
- Docker Compose
- pytest
- Swagger/OpenAPI through FastAPI
- Seed/demo data
- Audit logging
- Basic role-based authorization

## Explicitly Out of Scope for MVP

Do NOT implement these unless everything else is already complete and stable:

- React frontend
- Microservices
- Kubernetes
- Redis
- Celery
- MCP server
- WhatsApp
- Payments
- Complex authentication/JWT
- RAG/vector database
- Multi-tenant SaaS architecture
- Advanced event-driven architecture
- Complex design patterns
- Real ERP integration

Keep the implementation small enough to finish today.

---

# 3. Engineering Rules

## Rule 1 — Keep It Simple

Prefer:

- straightforward Python
- small functions
- explicit business logic
- readable SQLAlchemy models
- thin API routes
- simple service functions

Avoid abstractions that do not provide immediate value.

Do not build frameworks inside the project.

## Rule 2 — Business Logic Must Not Live in the Prompt

The LLM can decide:

- which tool to call
- in which order to call tools
- how to interpret natural-language intent

The application must decide:

- whether the user is authorized
- whether a request is valid
- stock calculations
- procurement status transitions
- approval permissions
- database writes

## Rule 3 — No Direct Database Access by the LLM

The model must never generate or execute arbitrary SQL.

The LLM can only use explicit tools.

## Rule 4 — Human Approval Is Mandatory

The AI may create:

```text
PENDING_PROCUREMENT
```

It must not autonomously turn it into:

```text
APPROVED
```

Approval/rejection is a normal application action controlled by authorization.

## Rule 5 — Test After Each Phase

Every phase must end with a working application and relevant tests.

Fix errors before continuing.

## Rule 6 — Do Not Rewrite Working Code Without Reason

Prefer incremental modifications.

Do not replace a working implementation merely because another architecture looks cleaner.

---

# 4. Target Architecture

```text
                    ┌─────────────────────┐
                    │      Swagger UI     │
                    │       /docs          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │       API Layer      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      AI Agent       │
                    │   Tool Orchestration│
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │ User Tools  │     │ Inventory   │     │ Procurement │
   │             │     │ Tools       │     │ Tools       │
   └─────────────┘     └─────────────┘     └─────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                        ┌─────────────┐
                        │ PostgreSQL  │
                        └──────┬──────┘
                               │
                               ▼
                        ┌─────────────┐
                        │ Audit Logs  │
                        └─────────────┘
```

---

# 5. Domain Model

Implement these entities first.

## User

Fields:

```text
id
name
department
role
```

Roles:

```text
EMPLOYEE
WAREHOUSE
PROCUREMENT
MANAGER
```

## Product

Fields:

```text
id
sku
name
description
unit
```

## Warehouse

Fields:

```text
id
name
location
```

## WarehouseLocation

Represents a physical storage location.

Fields:

```text
id
warehouse_id
section
shelf
bin
```

## Inventory

Represents how much of a product is stored at a location.

Fields:

```text
id
product_id
warehouse_location_id
quantity
```

## ProcurementRequest

Fields:

```text
id
user_id
product_id
quantity
priority
reason
status
created_at
```

Statuses:

```text
PENDING_PROCUREMENT
APPROVED
REJECTED
```

Priorities:

```text
LOW
NORMAL
HIGH
```

## AuditLog

Fields:

```text
id
user_id
request_id nullable
tool_name
arguments
result
created_at
```

For `arguments` and `result`, JSON/JSONB is preferred.

---

# 6. Required Agent Tools

Implement these tools with clear schemas and deterministic application behavior.

## User

```text
get_user(user_id)
```

## Product

```text
search_product(query)
get_product(product_id)
```

## Inventory

```text
check_stock(product_id)
find_product_locations(product_id)
```

## Procurement

```text
create_procurement_request(
    user_id,
    product_id,
    quantity,
    priority,
    reason
)

get_procurement_request(request_id)
```

Do not add more tools until these work correctly.

---

# 7. Expected Agent Behaviors

## Scenario A — Stock Question

User:

```text
How many SKF 6205 bearings do we have?
```

Expected behavior:

```text
search_product("SKF 6205")
    ↓
check_stock(product_id)
    ↓
natural-language answer
```

The agent should not invent stock values.

---

## Scenario B — Location Question

User:

```text
Where can I find SKF 6205?
```

Expected:

```text
search_product()
    ↓
find_product_locations()
    ↓
return warehouse + section + shelf + bin + quantity
```

---

## Scenario C — Insufficient Stock

User:

```text
We need 50 SKF 6205 bearings urgently.
```

Expected:

```text
search_product()
    ↓
check_stock()
    ↓
calculate shortage
    ↓
create_procurement_request()
    ↓
PENDING_PROCUREMENT
```

Example:

```text
Requested: 50
Available: 23
Shortage: 27
```

Create the procurement request for the shortage unless the product/workflow rules clearly require creating the full requested amount.

---

## Scenario D — Approval Boundary

User tries:

```text
Approve procurement request #42.
```

The agent must not bypass application authorization.

The application decides whether the authenticated/acting user may approve.

---

## Scenario E — Warehouse Update Boundary

If an employee asks to alter stock directly, do not invent an update tool for the MVP.

Only implement mutation tools that are actually required by the demo.

---

# 8. API Requirements

Implement these endpoints.

## Agent

```http
POST /agent/request
```

Request:

```json
{
  "user_id": 1,
  "message": "We need 50 SKF 6205 bearings urgently."
}
```

## Products

```http
GET /products
GET /products/{id}
```

## Inventory

```http
GET /inventory/{product_id}
```

## Warehouses

```http
GET /warehouses
GET /warehouses/{id}/locations
```

## Procurement

```http
GET /procurement/requests
POST /procurement/requests/{id}/approve
POST /procurement/requests/{id}/reject
GET /procurement/requests/{id}
```

## Audit

```http
GET /audit/{request_id}
```

---

# 9. Authorization Rules

Keep authorization simple and explicit.

```text
EMPLOYEE
  - search products
  - check stock
  - find locations
  - create procurement requests
  - read own procurement requests

WAREHOUSE
  - search products
  - check stock
  - find locations

PROCUREMENT
  - search products
  - check stock
  - view procurement requests

MANAGER
  - view procurement requests
  - approve requests
  - reject requests
```

Important:

Authorization must be enforced in application code, not delegated to the LLM.

---

# 10. Docker Requirements

The entire development environment must start with:

```bash
docker compose up --build
```

At minimum, Docker Compose must run:

```text
app
db
```

PostgreSQL configuration must come from environment variables.

Use:

```text
.env
.env.example
```

Do not commit real secrets.

The project should work without manually installing PostgreSQL.

---

# 11. Demo Data

Seed enough data to make the demo meaningful.

Minimum recommended records:

## Users

```text
1 | Ahmet | Maintenance | EMPLOYEE
2 | Ayse  | Procurement | PROCUREMENT
3 | Mehmet | Management | MANAGER
4 | Ali | Warehouse | WAREHOUSE
```

## Products

Example products:

```text
SKF-6205 | SKF 6205 Bearing
A4-80GSM  | A4 Paper
M12-BOLT  | M12 Bolt
```

## Warehouses

```text
Warehouse A
Warehouse B
```

## Locations

Example:

```text
Warehouse A / B / Shelf 14 / Bin 02
Warehouse A / C / Shelf 03 / Bin 11
Warehouse B / A / Shelf 07 / Bin 04
```

## Inventory

Ensure there is at least:

- one product with sufficient stock
- one product split across multiple warehouses
- one product with insufficient stock

This makes the agent demo more realistic.

---

# 12. Project Structure

Use a simple structure similar to:

```text
procure-ai/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── agent.py
│   │   ├── products.py
│   │   ├── inventory.py
│   │   ├── warehouse.py
│   │   ├── procurement.py
│   │   └── audit.py
│   │
│   ├── agent/
│   │   ├── service.py
│   │   ├── prompts.py
│   │   └── tools.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── db/
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

Do not create extra layers unless necessary.

---

# 13. Implementation Phases

Execute the following phases in order.

---

## PHASE 1 — Repository Scaffold

### Goal

Create the minimal runnable FastAPI application.

### Tasks

- initialize project
- create `app/`
- create FastAPI application
- create health endpoint
- create requirements file
- create Dockerfile
- create docker-compose.yml
- configure environment variables
- connect app container to PostgreSQL container

### Acceptance Criteria

```text
GET /health
```

returns something like:

```json
{
  "status": "ok"
}
```

and:

```bash
docker compose up --build
```

starts successfully.

### Stop Condition

Do not continue until the API and PostgreSQL connection work.

---

## PHASE 2 — Database Models

### Goal

Create the complete minimal domain model.

### Tasks

Implement:

- User
- Product
- Warehouse
- WarehouseLocation
- Inventory
- ProcurementRequest
- AuditLog

Add relationships where useful.

Do not overcomplicate the schema.

### Acceptance Criteria

- application starts
- tables are created
- SQLAlchemy can read/write records
- no relationship errors

---

## PHASE 3 — Seed Data

### Goal

Make the application immediately demoable.

### Tasks

Create a deterministic seed process.

Insert:

- users
- products
- warehouses
- locations
- inventory

Make sure at least one insufficient-stock scenario exists.

### Acceptance Criteria

A fresh Docker environment contains usable demo data.

Document how seed data is created.

---

## PHASE 4 — Business Services

### Goal

Implement deterministic business logic before involving the LLM.

### Tasks

Implement services for:

- product search
- inventory lookup
- location lookup
- procurement creation
- procurement retrieval
- approval/rejection
- audit persistence

Business rules must live here.

### Important

Stock shortage calculation must be deterministic.

Example:

```text
requested = 50
available = 23
shortage = max(50 - 23, 0)
```

Do not ask the LLM to perform authoritative inventory calculations.

### Acceptance Criteria

All core operations work without the AI agent.

---

## PHASE 5 — API Endpoints

### Goal

Expose the business operations.

### Tasks

Implement the endpoints from section 8.

Validate input with Pydantic.

Return appropriate HTTP status codes.

### Acceptance Criteria

All endpoints are visible in:

```text
/docs
```

and can be demonstrated without the AI.

---

## PHASE 6 — Authorization

### Goal

Enforce simple role boundaries.

### Tasks

Implement a minimal authorization dependency/helper.

Do not implement complex authentication unless required.

For the MVP, using a demo `user_id`/acting user mechanism is acceptable as long as the authorization logic itself is real and testable.

### Tests

At minimum:

```text
EMPLOYEE cannot approve
MANAGER can approve
EMPLOYEE can create request
```

### Acceptance Criteria

Unauthorized business actions fail with a clear HTTP error.

---

## PHASE 7 — Agent Tools

### Goal

Wrap business services as controlled LLM tools.

### Tasks

Implement:

```text
get_user
search_product
get_product
check_stock
find_product_locations
create_procurement_request
get_procurement_request
```

Every tool must:

- validate inputs
- call application services
- return structured data
- write an audit log where appropriate

The tool layer must not contain duplicated business rules.

### Acceptance Criteria

Tools can be called from Python without the LLM.

---

## PHASE 8 — LLM Agent

### Goal

Connect the tool layer to the LLM.

### Tasks

Implement agent orchestration.

The agent must:

1. receive a natural-language request
2. decide whether tools are needed
3. call appropriate tools
4. use tool results
5. continue calling tools when necessary
6. produce a concise final response

Use a strong system prompt that states:

- available tools
- role of the agent
- no arbitrary SQL
- no invented inventory facts
- no approval bypass
- use tools when factual data is required

### Important

Do not create a complex autonomous framework.

A simple tool-calling loop is preferred.

### Acceptance Criteria

These scenarios work:

```text
"What is the stock of SKF 6205?"
"Where is SKF 6205?"
"We need 50 SKF 6205 bearings urgently."
```

---

## PHASE 9 — Audit Logging

### Goal

Make agent behavior traceable.

### Tasks

Record:

- user
- request id when available
- tool name
- arguments
- result
- timestamp

Avoid storing secrets.

### Acceptance Criteria

A completed agent interaction leaves an understandable audit trail.

---

## PHASE 10 — Tests

### Goal

Prove that the important behavior works.

### Minimum Tests

### Agent/tool behavior

- product search
- stock lookup
- location lookup
- shortage detection
- procurement creation

### Authorization

- employee cannot approve
- manager can approve

### Procurement workflow

- created request starts as `PENDING_PROCUREMENT`
- approved request becomes `APPROVED`
- rejected request becomes `REJECTED`

### Audit

- tool invocation is recorded

### Acceptance Criteria

```bash
pytest
```

passes.

Fix test failures before proceeding.

---

## PHASE 11 — End-to-End Demo Verification

### Goal

Verify the entire story from a clean environment.

### Steps

1. Remove local containers/volumes if needed.
2. Run:

```bash
docker compose up --build
```

3. Open:

```text
http://localhost:8000/docs
```

4. Seed data.
5. Execute the natural-language agent request.
6. Verify tool calls.
7. Verify inventory response.
8. Verify procurement request creation.
9. Approve as manager.
10. Read audit logs.

### Required Demo Scenario

Use:

```text
We need 50 SKF 6205 bearings urgently for maintenance.
Check whether we have enough in stock and create a procurement request for anything missing.
```

Expected flow:

```text
search_product
      ↓
check_stock
      ↓
calculate shortage
      ↓
create_procurement_request
      ↓
PENDING_PROCUREMENT
      ↓
human manager approves
      ↓
APPROVED
```

---

## PHASE 12 — README and Repository Cleanup

### Goal

Make the GitHub repository easy to evaluate.

README must clearly explain:

- what ProcureAI is
- why it exists
- architecture
- agent/tool model
- warehouse features
- procurement workflow
- authorization
- human-in-the-loop
- auditability
- Docker setup
- example API usage
- example agent conversation
- evaluation/tests
- future extensions

Also include a concise architecture diagram.

Remove:

- dead files
- temporary scripts
- debug print statements
- unused dependencies
- secrets
- broken comments
- generated junk

Run the complete test suite one final time.

---

# 14. Final Demo Checklist

Before considering the project complete, verify all of these:

## Infrastructure

- [ ] `docker compose up --build` works
- [ ] PostgreSQL starts automatically
- [ ] API starts automatically
- [ ] `/docs` loads

## Data

- [ ] Users exist
- [ ] Products exist
- [ ] Warehouses exist
- [ ] Locations exist
- [ ] Inventory exists
- [ ] Multi-warehouse example exists
- [ ] Insufficient-stock example exists

## Agent

- [ ] Agent accepts natural-language requests
- [ ] Agent uses tools
- [ ] Agent does not invent stock
- [ ] Agent does not use arbitrary SQL
- [ ] Agent can search products
- [ ] Agent can check stock
- [ ] Agent can locate products
- [ ] Agent can create procurement requests

## Workflow

- [ ] New requests become `PENDING_PROCUREMENT`
- [ ] Approval is human/application controlled
- [ ] Unauthorized approval fails
- [ ] Approved requests become `APPROVED`
- [ ] Rejected requests become `REJECTED`

## Audit

- [ ] Tool calls are logged
- [ ] Logs include arguments/results
- [ ] Secrets are not logged

## Quality

- [ ] pytest passes
- [ ] no obvious dead code
- [ ] no hardcoded API key
- [ ] `.env` is ignored by git
- [ ] `.env.example` exists
- [ ] README is complete

---

# 15. Git Workflow

Make small commits after successful phases.

Recommended commits:

```text
chore: initialize FastAPI project
feat: add database models
feat: add seed data
feat: implement warehouse services
feat: implement procurement workflow
feat: add authorization
feat: add agent tools
feat: add LLM tool-calling agent
feat: add audit logging
test: add core workflow tests
docs: add project documentation
```

Do not commit secrets.

---

# 16. Definition of Done

The project is done when a reviewer can clone the repository and run:

```bash
docker compose up --build
```

then open:

```text
http://localhost:8000/docs
```

and verify that a natural-language request can:

```text
understand the request
        ↓
search the product
        ↓
check inventory
        ↓
locate stock
        ↓
calculate shortage
        ↓
create procurement request
        ↓
wait for human approval
        ↓
produce an auditable result
```

The most important outcome is not the number of files or features.

The important outcome is demonstrating:

> **An LLM can safely operate real business workflows through controlled tools, application-level authorization, and human approval.**

---

# 17. Agent Instructions

When implementing this project, follow these rules:

1. Read this entire document before starting.
2. Work phase-by-phase.
3. Do not skip acceptance criteria.
4. Keep the implementation simple.
5. Do not add out-of-scope infrastructure.
6. Prefer existing code over rewrites.
7. Test after every meaningful change.
8. Fix errors before moving forward.
9. Never commit secrets.
10. Keep business logic outside the LLM prompt.
11. Never give the LLM unrestricted database access.
12. Never allow the AI to bypass application authorization.
13. Never let the AI autonomously approve procurement requests.
14. Use structured tool inputs/outputs.
15. Update README when behavior or setup changes.
16. At the end of each phase, briefly report:
   - what was implemented
   - what was tested
   - any known limitation
   - the next phase

**Do not wait for additional instructions between phases unless a real blocker makes continuing impossible.**

Start with **PHASE 1 — Repository Scaffold**.
