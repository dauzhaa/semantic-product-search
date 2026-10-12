"""Controlled scores test search logic without loading model weights."""
from copy import deepcopy

import numpy as np
import pytest

from semantic_search import semantic_search


class FakeModel:
    def encode(self, texts):
        return np.array([[1.0, 0.0] for _ in texts])

    def similarity(self, query_embeddings, product_embeddings):
        return query_embeddings @ product_embeddings.T


@pytest.fixture
def resources():
    products = [{"id": letter} for letter in "abcdefg"]
    embeddings = np.array([[score, 0.0] for score in [0.2, 0.9, 0.6, 0.8, 0.1, 0.7, 0.4]])
    mapping = {product["id"]: i for i, product in enumerate(products)}
    return products, embeddings, mapping


def test_descending_ranking_and_embedding_alignment(resources):
    products, embeddings, mapping = resources
    eligible = [products[2], products[0], products[1]]
    results = semantic_search("audio", eligible, FakeModel(), embeddings, mapping)
    assert [p["id"] for p in results] == ["b", "c", "a"]


def test_ineligible_highest_score_is_excluded(resources):
    products, embeddings, mapping = resources
    eligible = [products[0], products[2]]
    results = semantic_search("audio", eligible, FakeModel(), embeddings, mapping)
    assert [p["id"] for p in results] == ["c", "a"]


def test_returns_only_best_five(resources):
    products, embeddings, mapping = resources
    results = semantic_search("audio", products, FakeModel(), embeddings, mapping)
    assert [p["id"] for p in results] == ["b", "d", "f", "c", "g"]


def test_empty_eligible_returns_before_using_resources():
    # None resources deliberately fail if search tries to use them.
    assert semantic_search("audio", [], None, None, None) == []


def test_search_preserves_inputs(resources):
    products, embeddings, mapping = resources
    eligible = [products[2], products[0], products[1]]
    before_products = deepcopy(products)
    before_eligible = deepcopy(eligible)
    before_embeddings = embeddings.copy()
    before_mapping = mapping.copy()
    semantic_search("audio", eligible, FakeModel(), embeddings, mapping)
    assert products == before_products
    assert eligible == before_eligible
    assert mapping == before_mapping
    np.testing.assert_array_equal(embeddings, before_embeddings)
