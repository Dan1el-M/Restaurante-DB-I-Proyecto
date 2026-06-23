"""Graph export endpoints used by the Neo4J loader."""

from decimal import Decimal

from fastapi import APIRouter, Depends

from backend.dao import BaseDAO, field_value
from backend.database import get_dao

router = APIRouter(prefix="/graph", tags=["Neo4J"])


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(row, fields):
    return {field: clean_value(field_value(row, field)) for field in fields}


@router.get("/export")
def export_graph_data(dao: BaseDAO = Depends(get_dao)):
    """Export operational records required by Neo4J from the active DAO."""
    roles = [row_to_dict(row, ["role_id", "role_name"]) for row in dao.list_roles()]
    role_by_id = {role["role_id"]: role["role_name"] for role in roles}

    users = [row_to_dict(row, ["user_id", "user_name", "keycloak_id", "role_id"]) for row in dao.list_users()]
    for user in users:
        user["role_name"] = role_by_id.get(user["role_id"])

    restaurants = [
        row_to_dict(row, ["restaurant_id", "restaurant_name", "admin_id", "restaurant_status"])
        for row in dao.list_restaurants()
    ]
    products = [
        row_to_dict(row, ["menu_id", "dish_name", "category", "price", "restaurant_id"])
        for row in dao.list_menus()
    ]
    order_items = [
        row_to_dict(row, ["order_item_id", "order_id", "menu_id", "quantity", "price"])
        for row in dao.list_order_items()
    ]
    totals = {}
    for item in order_items:
        totals[item["order_id"]] = totals.get(item["order_id"], 0) + float(item["price"]) * int(item["quantity"])

    orders = [row_to_dict(row, ["order_id", "table_id", "client_id", "order_type", "restaurant_id"]) for row in dao.list_orders()]
    for order in orders:
        order["total"] = totals.get(order["order_id"], 0)

    return {
        "roles": roles,
        "users": users,
        "restaurants": restaurants,
        "products": products,
        "orders": orders,
        "order_items": order_items,
    }
