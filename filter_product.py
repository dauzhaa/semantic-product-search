import json

def parse_products(filename):
    with open(filename, encoding="utf-8") as f:
        product_list = json.load(f)

    return product_list


def matching_prod(product_list, category=None, max_price=None, in_stock=None):

    res = []

    for p in product_list:

        if category is not None and p['category'] != category:
            continue

        if max_price is not None and p['price'] > max_price:
            continue

        if in_stock is not None and p['in_stock'] != in_stock:
            continue

        res.append(p)


    return res

# if __name__ == "__main__":
#     p = parse_products("products.json")
#     print(matching_prod(p, 'headphones', 20000, True))
#     print('')
#     print(matching_prod(p))