def key_search(query, product_list):
    q = query.lower().split()
    score = []
    for product in product_list:
        set_name = set(product.get('name').lower().split())
        set_description = set(product.get('description').lower().split())
        words = set_name | set_description
        temp_score = len(set(q) & words)
        if temp_score > 0:
            score.append((product, temp_score))


    score.sort(key=lambda x: x[1], reverse=True)
    top5 = score[:5]
    res = [product for product, count in top5]
    return res

# if __name__ == '__main__':
#     from filter_product import parse_products

#     products = parse_products('products.json')
#     # key_search("waterproof speaker", products)
#     print(key_search("speaker", products))
#     # print(key_search("refrigerator", products))
