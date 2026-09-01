from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import engine, Base
from app.api import products, inventory, warehouse, procurement, audit, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so Base knows about them before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Seed demo data (idempotent — skips if data already present)
    from app.db.seed import seed
    seed()
    yield


app = FastAPI(
    title="ProcureAI",
    description="AI-powered procurement and warehouse assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(agent.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(warehouse.router)
app.include_router(procurement.router)
app.include_router(audit.router)


@app.get("/health")
def health():
    return {"status": "ok"}
