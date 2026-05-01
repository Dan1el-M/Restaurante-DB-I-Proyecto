import os

from fastapi import APIRouter, Depends
from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.app.cache.cache_service import get_cache, set_cache, delete_cache_pattern
from backend.dao import BaseDAO
from backend.database import get_dao
from backend.app.search.search_service import (
    create_index,
    index_product,
    refresh_index,
    search_products,
    search_by_category,
)

router = APIRouter(prefix="/search", tags=["Search"])
SEARCH_CACHE_PREFIX = "search:products"
SEARCH_CACHE_TTL_SECONDS = int(os.getenv("SEARCH_CACHE_TTL_SECONDS", 60))


def normalize_cache_value(value: str):
    return value.strip().lower()


@router.get("/products")
def search_products_endpoint(q: str, token_payload=Depends(get_current_user)):
    normalized_query = normalize_cache_value(q)
    cache_key = f"{SEARCH_CACHE_PREFIX}:text:{normalized_query}"

    cached_data = get_cache(cache_key)
    if cached_data is not None:
        print("SEARCH CACHE HIT")
        return cached_data

    print("SEARCH CACHE MISS")
    results = search_products(q)
    set_cache(cache_key, results, ttl=SEARCH_CACHE_TTL_SECONDS)

    return results


@router.get("/products/category/{category}")
def search_products_by_category(category: str, token_payload=Depends(get_current_user)):
    normalized_category = normalize_cache_value(category)
    cache_key = f"{SEARCH_CACHE_PREFIX}:category:{normalized_category}"

    cached_data = get_cache(cache_key)
    if cached_data is not None:
        print("SEARCH CACHE HIT")
        return cached_data

    print("SEARCH CACHE MISS")
    results = search_by_category(category)
    set_cache(cache_key, results, ttl=SEARCH_CACHE_TTL_SECONDS)

    return results


@router.post("/reindex")
def reindex_products(token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    create_index(recreate=True)

    menus = dao.list_menus()

    for menu in menus:
        index_product(menu)

    refresh_index()
    delete_cache_pattern(f"{SEARCH_CACHE_PREFIX}:*")

    return {
        "message": "Productos reindexados correctamente",
        "total": len(menus),
    }
