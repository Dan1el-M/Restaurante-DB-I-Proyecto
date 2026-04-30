from backend.app.search.elasticsearch_client import es_client

INDEX_NAME = "products"


def create_index():
    if es_client.indices.exists(index=INDEX_NAME):
        return

    es_client.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "menu_id": {"type": "integer"},
                "dish_name": {"type": "text"},
                "category": {"type": "keyword"},
                "description": {"type": "text"},
                "price": {"type": "float"},
                "restaurant_id": {"type": "integer"},
            }
        },
    )


def index_product(menu: dict):
    description = menu.get("description") or "Producto sin descripción"

    document = {
        "menu_id": menu.get("menu_id"),
        "dish_name": menu.get("dish_name"),
        "category": menu.get("category", "general"),
        "description": description,
        "price": float(menu.get("price", 0)),
        "restaurant_id": menu.get("restaurant_id"),
    }

    es_client.index(
        index=INDEX_NAME,
        id=menu.get("menu_id"),
        document=document,
    )


def search_products(text: str):
    result = es_client.search(
        index=INDEX_NAME,
        query={
            "multi_match": {
                "query": text,
                "fields": ["dish_name", "category", "description"],
            }
        },
    )

    return [hit["_source"] for hit in result["hits"]["hits"]]


def search_by_category(category: str):
    result = es_client.search(
        index=INDEX_NAME,
        query={
            "term": {
                "category": category
            }
        },
    )

    return [hit["_source"] for hit in result["hits"]["hits"]]