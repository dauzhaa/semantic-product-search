from fastapi import FastAPI
from pydantic import BaseModel, Field
import filter_product
from contextlib import asynccontextmanager
from pathlib import Path
from semantic_search import load_search_resources
import semantic_search
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    catalog_path = Path(__file__).parent / "products.json"
    app.state.search_resources = load_search_resources(catalog_path)
    yield
    app.state.search_resources.clear()

app = FastAPI(lifespan=lifespan)

class SearchFilters(BaseModel):
    category: str | None = None
    max_price: int | None = Field(default=None, ge=0)
    in_stock: bool | None = None
    query: str | None = None

@app.post("/search")
def search_p(filters: SearchFilters):
    resources = app.state.search_resources
    p_lst = resources["products"]
    product_filter = filter_product.matching_prod(
        p_lst,
        category=filters.category,
        max_price=filters.max_price,
        in_stock=filters.in_stock,
    )

    if filters.query and filters.query.strip():
        return semantic_search.semantic_search(filters.query, product_filter, resources["model"], resources["embeddings"], resources["index_by_id"])

    return product_filter

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/products")
def catalog():
    return app.state.search_resources["products"]

@app.get("/")
def home():
    html_path = Path(__file__).parent / "static" / "index.html"
    return FileResponse(html_path)