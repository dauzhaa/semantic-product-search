import filter_product
import copy
from pathlib import Path

p = filter_product.parse_products(
    Path(__file__).parent / "fixtures" / "products.json"
)

def test_price1():
    res = filter_product.matching_prod(p, None, 20000)
    ids = [prod['id'] for prod in res]
    assert ids == ["p001", "p002", "p004", "p005"]

def test_p002():
    res = filter_product.matching_prod(p, 'headphones', 20000, False)
    ids = [prod['id'] for prod in res]
    assert ids == ["p002"]

def test_price2():
    res = filter_product.matching_prod(p, None, 10000)
    ids = [prod['id'] for prod in res]
    assert ids == []

def test_no_filter():
    res = filter_product.matching_prod(p)
    ids = [prod['id'] for prod in res]
    assert ids == ["p001", "p002", "p003", "p004", "p005", "p006"]

def test_category():
    res = filter_product.matching_prod(p, 'headphones')
    ids = [prod['id'] for prod in res]
    assert ids == ["p001", "p002", "p003"]

def test_stock_only():
    res = filter_product.matching_prod(p, None, None, False)
    ids = [prod['id'] for prod in res]
    assert ids == ["p002", "p006"]

def test_copy():
    temp = copy.deepcopy(p)
    res = filter_product.matching_prod(p, category="speakers")
    assert len(res) < len(p)
    assert p == temp
    assert len(p) == 6