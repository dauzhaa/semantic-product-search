"""API contract tests; startup uses the fixed catalog and a fake model."""
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

import main


class FakeModel:
    def encode(self, texts):
        return np.array([[1.0, 0.0] for _ in texts])

    def similarity(self, query_embeddings, product_embeddings):
        return query_embeddings @ product_embeddings.T


@pytest.fixture
def client(monkeypatch):
    path = Path(__file__).parent / "fixtures" / "products.json"
    products = main.filter_product.parse_products(path)
    resources = {
        "products": products,
        "model": FakeModel(),
        # Higher price is unrelated to relevance: these are arbitrary test scores.
        # The excluded p006 intentionally has the highest score.
        "embeddings": np.array([[s, 0.0] for s in [0.2, 0.3, 0.4, 0.6, 0.8, 0.9]]),
        "index_by_id": {p["id"]: i for i, p in enumerate(products)},
    }
    monkeypatch.setattr(main, "load_search_resources", lambda catalog_path: resources)
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.mark.parametrize("query_fields", [{}, {"query": None}, {"query": ""}, {"query": " \t\n"}])
def test_blank_queries_return_all_eligible_without_ranking(client, monkeypatch, query_fields):
    def unexpected_search(*args, **kwargs):
        pytest.fail("Blank queries must not invoke semantic ranking")

    monkeypatch.setattr(main.semantic_search, "semantic_search", unexpected_search)
    response = client.post("/search", json=query_fields)
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p001", "p002", "p003", "p004", "p005", "p006"]
    filtered = client.post("/search", json={**query_fields, "category": "speakers", "max_price": 20000, "in_stock": True})
    assert filtered.status_code == 200
    assert [p["id"] for p in filtered.json()] == ["p004", "p005"]


def test_query_ranks_only_products_passing_all_filters(client):
    response = client.post("/search", json={"query": "speaker", "category": "speakers", "max_price": 20000, "in_stock": True})
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p005", "p004"]


def test_query_returns_five_results(client):
    response = client.post("/search", json={"query": "audio"})
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p006", "p005", "p004", "p003", "p002"]


@pytest.mark.parametrize("query", ["speaker", ""])
def test_no_eligible_products(client, query):
    response = client.post("/search", json={"query": query, "category": "nonexistent"})
    assert response.status_code == 200
    assert response.json() == []


def test_negative_price_is_rejected(client):
    response = client.post("/search", json={"max_price": -1})
    assert response.status_code == 422
    assert any(error["loc"] == ["body", "max_price"] for error in response.json()["detail"])


def test_zero_price_is_accepted(client):
    response = client.post("/search", json={"max_price": 0})
    assert response.status_code == 200
    assert response.json() == []


def test_null_price_disables_price_filter(client):
    response = client.post("/search", json={"max_price": None})
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p001", "p002", "p003", "p004", "p005", "p006"]


def test_false_stock_means_out_of_stock(client):
    response = client.post("/search", json={"in_stock": False})
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p002", "p006"]


def test_search_does_not_change_catalog(client):
    before = client.get("/products").json()
    response = client.post("/search", json={"query": "speaker", "category": "speakers"})
    assert response.status_code == 200
    assert client.get("/products").json() == before
