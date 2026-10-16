from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .db import Base, engine, get_db
from .models import Product
from .schemas import ProductCreate, ProductOut, ProductUpdate, StatsOut

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production containers run Alembic before Uvicorn; create_all keeps local runs self-contained.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

def get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def ensure_sku_free(sku: str, db: Session, current_id: int | None = None):
    existing = db.scalar(select(Product).where(Product.sku == sku))
    if existing and existing.id != current_id:
        raise HTTPException(status_code=409, detail=f"SKU '{sku}' already exists")

@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "UP"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(func.count(Product.id)))
    return {"status": "READY"}

@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return list(db.scalars(select(Product).order_by(Product.id.desc())))

@app.get("/api/products/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Product.status, func.count(Product.id)).group_by(Product.status)).all()
    counts = {status: count for status, count in rows}
    return StatsOut(
        total=sum(counts.values()),
        inStock=counts.get("IN_STOCK", 0),
        lowStock=counts.get("LOW_STOCK", 0),
        outOfStock=counts.get("OUT_OF_STOCK", 0),
    )

@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_or_404(product_id, db)

@app.post("/api/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    ensure_sku_free(payload.sku, db)
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.put("/api/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "sku" in changes:
        ensure_sku_free(changes["sku"], db, current_id=product_id)
    for key, value in changes.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

@app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    db.delete(product)
    db.commit()
