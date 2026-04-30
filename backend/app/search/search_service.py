from backend.app.search.elasticsearch_client import es_client

INDEX_NAME = "products"
DEFAULT_CATEGORY = "general"
DEFAULT_DESCRIPTION = "Producto sin descripción"


def product_value(product, field_name: str, default=None):
    if isinstance(product, dict):
        return product.get(field_name, default)
    return getattr(product, field_name, default)


def create_index(recreate: bool = False):
    if recreate and es_client.indices.exists(index=INDEX_NAME):
        es_client.indices.delete(index=INDEX_NAME)

    if es_client.indices.exists(index=INDEX_NAME):
        return

    es_client.indices.create(
        index=INDEX_NAME,
        settings={
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        mappings={
            "properties": {
                "menu_id": {"type": "integer"},
                "dish_name": {"type": "text"},
                "category": {
                    "type": "text",
                    "fields": {
                        "raw": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                        }
                    },
                },
                "description": {"type": "text"},
                "price": {"type": "float"},
                "restaurant_id": {"type": "integer"},
            }
        },
    )


def index_product(menu):
    description = product_value(menu, "description") or DEFAULT_DESCRIPTION
    category = product_value(menu, "category") or DEFAULT_CATEGORY
    menu_id = product_value(menu, "menu_id")

    document = {
        "menu_id": menu_id,
        "dish_name": product_value(menu, "dish_name"),
        "category": category,
        "description": description,
        "price": float(product_value(menu, "price", 0)),
        "restaurant_id": product_value(menu, "restaurant_id"),
    }

    es_client.index(
        index=INDEX_NAME,
        id=menu_id,
        document=document,
    )


def refresh_index():
    es_client.indices.refresh(index=INDEX_NAME)


def search_products(text: str):
    create_index()

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
    create_index()

    result = es_client.search(
        index=INDEX_NAME,
        query={
            "term": {
                "category.raw": category.lower()
            }
        },
    )

    return [hit["_source"] for hit in result["hits"]["hits"]]
