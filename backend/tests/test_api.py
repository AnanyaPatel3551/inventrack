def create(client, product):
    response = client.post("/api/products", json=product)
    assert response.status_code == 201
    return response.json()

def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}

def test_ready(client):
    assert client.get("/ready").json() == {"status": "READY"}

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "InvenTrack API"

def test_create_product(client, sample_product):
    body = create(client, sample_product)
    assert body["id"] > 0
    assert body["sku"] == "ELEC-1001"
    assert body["price"] == 19.99
    assert body["status"] == "IN_STOCK"

def test_create_product_rejects_duplicate_sku(client, sample_product):
    create(client, sample_product)
    response = client.post("/api/products", json={**sample_product, "name": "Another mouse"})
    assert response.status_code == 409

def test_create_product_rejects_negative_quantity(client, sample_product):
    response = client.post("/api/products", json={**sample_product, "quantity": -5})
    assert response.status_code == 422

def test_create_product_rejects_unknown_status(client, sample_product):
    response = client.post("/api/products", json={**sample_product, "status": "DISCONTINUED"})
    assert response.status_code == 422

def test_list_and_get_product(client, sample_product):
    created = create(client, sample_product)
    listing = client.get("/api/products").json()
    assert [p["id"] for p in listing] == [created["id"]]
    single = client.get(f"/api/products/{created['id']}")
    assert single.status_code == 200
    assert single.json()["name"] == "Wireless Mouse"

def test_get_missing_product_returns_404(client):
    assert client.get("/api/products/9999").status_code == 404

def test_update_product_status(client, sample_product):
    created = create(client, sample_product)
    response = client.put(f"/api/products/{created['id']}", json={"status": "LOW_STOCK", "quantity": 3})
    assert response.status_code == 200
    assert response.json()["status"] == "LOW_STOCK"
    assert response.json()["quantity"] == 3
    assert response.json()["name"] == "Wireless Mouse"

def test_delete_product(client, sample_product):
    created = create(client, sample_product)
    assert client.delete(f"/api/products/{created['id']}").status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404

def test_stats(client, sample_product):
    create(client, sample_product)
    create(client, {**sample_product, "sku": "ELEC-1002", "status": "LOW_STOCK"})
    create(client, {**sample_product, "sku": "ELEC-1003", "status": "OUT_OF_STOCK"})
    create(client, {**sample_product, "sku": "ELEC-1004", "status": "OUT_OF_STOCK"})
    assert client.get("/api/products/stats").json() == {"total": 4, "inStock": 1, "lowStock": 1, "outOfStock": 2}

def test_metrics_endpoint(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
