from fastapi.testclient import TestClient
from main import app
from pathlib import Path

import pytest
import main
import numpy as np

class FakeModel:
    def encode(self, texts):
        return np.array([[1.0, 0.0] for _ in texts])

    def similarity(self, query_embeddings, product_embeddings):
        return query_embeddings @ product_embeddings.T

@pytest.fixture()
def use_test_catalog(monkeypatch):
    fixture_path = Path(__file__).parent / "fixtures" / "products.json"
    products = main.filter_product.parse_products(fixture_path)

    model = FakeModel()
    texts = [
        f'{product["name"]}. {product["description"]}'
        for product in products
    ]
    embeddings = model.encode(texts)

    index_by_id = {
        product["id"]: index
        for index, product in enumerate(products)
    }

    resources = {
        "products": products,
        "model": model,
        "embeddings": embeddings,
        "index_by_id": index_by_id,
    }

    monkeypatch.setattr(
        main,
        "load_search_resources",
        lambda catalog_path: resources,
    )

@pytest.fixture
def client(use_test_catalog):
    with TestClient(app) as client:
        yield client

def test_client(client):
    response = client.post(
    "/search",
    json={"category": "headphones", "max_price": 20000, "in_stock": True},
)
    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == ["p001"]

def test_search_without_filter(client):
    response = client.post(
    "/search",
    json={},
)
    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == ["p001", "p002", "p003", "p004", "p005", "p006"]

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_catalog(client):
    response = client.get("/products")
    assert response.status_code == 200

    lst = response.json()
    assert [prod["id"] for prod in lst] == ["p001", "p002", "p003", "p004", "p005", "p006"]

def test_search_query(client):
    response = client.post(
    "/search",
    json={
    "query": "speaker",
    "category": "speakers",
    "max_price": 20000,
    "in_stock": True,
},
)
    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == ["p004", "p005"]
