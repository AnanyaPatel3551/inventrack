import os

# Point the app at a throwaway SQLite file before anything imports app.config
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

@pytest.fixture(scope="session")
def client():
    # Start from an empty schema in case an old test.db is lying around
    Base.metadata.drop_all(bind=engine)
    # Entering the context runs the app lifespan, which creates the tables
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture()
def new_product():
    # The database is shared across the session, so every product gets its own SKU
    def build(**overrides):
        product = {
            "name": "Wireless Mouse",
            "sku": f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "category": "Electronics",
            "quantity": 40,
            "price": 19.99,
            "supplier": "Logi Distributors",
            "status": "IN_STOCK",
        }
        product.update(overrides)
        return product
    return build
