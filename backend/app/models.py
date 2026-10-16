from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="General")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    # Stored as an exact NUMERIC(10,2) in Postgres, returned to Python as a float
    price: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), default=0)
    supplier: Mapped[str] = mapped_column(String(150), default="")
    status: Mapped[str] = mapped_column(String(20), default="IN_STOCK")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
