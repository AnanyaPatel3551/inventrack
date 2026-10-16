import os

# Point the app at a throwaway SQLite file before anything imports app.config
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def sample_product():
    return {
        "name": "Wireless Mouse",
        "sku": "ELEC-1001",
        "category": "Electronics",
        "quantity": 40,
        "price": 19.99,
        "supplier": "Logi Distributors",
        "status": "IN_STOCK",
    }
