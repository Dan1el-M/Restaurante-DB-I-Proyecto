from fastapi import APIRouter, Depends
from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO
from backend.database import get_dao
from backend.app.search.search_service import (
    create_index,
    index_product,
    search_products,
    search_by_category,
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/products")
def search_products_endpoint(q: str, token_payload=Depends(get_current_user)):
    return search_products(q)


@router.get("/products/category/{category}")
def search_products_by_category(category: str, token_payload=Depends(get_current_user)):
    return search_by_category(category)


@router.post("/reindex")
def reindex_products(token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    create_index()

    menus = dao.list_menus()

    for menu in menus:
        index_product(menu)

    return {
        "message": "Productos reindexados correctamente",
        "total": len(menus),
    }