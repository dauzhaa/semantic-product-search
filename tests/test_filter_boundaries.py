"""Edge cases supplement the existing fixture-based filtering tests."""
import pytest

from filter_product import matching_prod


@pytest.mark.parametrize("filters, expected", [
    ({"max_price": 0}, ["free"]),
    ({"max_price": 1}, ["free", "paid"]),
    ({"in_stock": False}, ["free"]),
    ({"in_stock": True}, ["paid"]),
    ({"category": None, "max_price": None, "in_stock": None}, ["free", "paid"]),
    ({"category": ""}, []),
])
def test_optional_filters_and_boundaries(filters, expected):
    products = [
        {"id": "free", "category": "speakers", "price": 0, "in_stock": False},
        {"id": "paid", "category": "speakers", "price": 1, "in_stock": True},
    ]
    assert [p["id"] for p in matching_prod(products, **filters)] == expected


def test_empty_catalog():
    assert matching_prod([], category="speakers", max_price=0, in_stock=False) == []
