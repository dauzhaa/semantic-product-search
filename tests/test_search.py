from keyword_search import key_search


def test_speaker():
    product_list = [
        {"id": "a", "name": "Bluetooth Speaker", "description": "Portable audio"},
        {"id": "b", "name": "Desk Lamp", "description": "Warm light"},
        {"id": "c", "name": "Waterproof Speaker", "description": "Shower audio"},
    ]

    search = key_search("waterproof speaker", product_list)
    ids = [prod["id"] for prod in search]

    assert ids == ["c", "a"]