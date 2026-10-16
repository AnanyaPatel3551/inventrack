def create(client, product):
    response = client.post("/api/products", json=product)
    assert response.status_code == 201, response.text
    return response.json()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "InvenTrack API"
    assert response.json()["docs"] == "/docs"

def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}

def test_create_product(client, new_product):
    payload = new_product()
    body = create(client, payload)
    assert body["id"] > 0
    assert body["sku"] == payload["sku"]
    assert body["price"] == 19.99
    assert body["quantity"] == 40
    assert body["status"] == "IN_STOCK"
    assert "created_at" in body

def test_create_product_with_empty_name_returns_422(client, new_product):
    response = client.post("/api/products", json=new_product(name=""))
    assert response.status_code == 422

def test_create_product_with_duplicate_sku_returns_409(client, new_product):
    payload = new_product()
    create(client, payload)
    response = client.post("/api/products", json={**payload, "name": "Another mouse"})
    assert response.status_code == 409

def test_list_get_and_404(client, new_product):
    created = create(client, new_product(name="Office Chair", category="Furniture"))

    listing = client.get("/api/products")
    assert listing.status_code == 200
    assert created["id"] in [p["id"] for p in listing.json()]

    single = client.get(f"/api/products/{created['id']}")
    assert single.status_code == 200
    assert single.json()["name"] == "Office Chair"

    missing = client.get("/api/products/999999")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Product not found"

def test_update_product_and_stats(client, new_product):
    created = create(client, new_product())
    before = client.get("/api/products/stats").json()

    response = client.put(f"/api/products/{created['id']}", json={"status": "LOW_STOCK", "quantity": 3})
    assert response.status_code == 200
    assert response.json()["status"] == "LOW_STOCK"
    assert response.json()["quantity"] == 3
    # Fields that were not sent stay unchanged
    assert response.json()["name"] == created["name"]

    after = client.get("/api/products/stats").json()
    assert after["total"] == before["total"]
    assert after["inStock"] == before["inStock"] - 1
    assert after["lowStock"] == before["lowStock"] + 1
    assert after["outOfStock"] == before["outOfStock"]
    assert after["total"] == after["inStock"] + after["lowStock"] + after["outOfStock"]

def test_delete_product(client, new_product):
    created = create(client, new_product(status="OUT_OF_STOCK", quantity=0))
    total_before = client.get("/api/products/stats").json()["total"]

    assert client.delete(f"/api/products/{created['id']}").status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404
    assert client.delete(f"/api/products/{created['id']}").status_code == 404
    assert client.get("/api/products/stats").json()["total"] == total_before - 1

def test_metrics_endpoint(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
