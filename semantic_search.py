import filter_product
from sentence_transformers import SentenceTransformer

def semantic_search(query, eligible, model, embeddings, index_id):
    if not eligible:
        return []

    eligible_indices = [index_id[product["id"]] for product in eligible]
    eligible_embeddings = embeddings[eligible_indices]

    query_embedding = model.encode([query])
    similarities = model.similarity(query_embedding, eligible_embeddings)
    scores = similarities[0].tolist()

    ranked = sorted(
        zip(eligible, scores),
        key=lambda pair: pair[1],
        reverse=True,
    )

    return [product for product, score in ranked[:5]]


def load_search_resources(catalog_path):
    products = filter_product.parse_products(catalog_path)
    model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu",
)
    name_descrp = [f'{prod["name"]}. {prod["description"]}' for prod in products]
    embeddings = model.encode(name_descrp)
    index_by_id = {product["id"]: index for index, product in enumerate(products)}
    return {
        "products": products,
        "model": model,
        "embeddings": embeddings,
        "index_by_id": index_by_id,}

