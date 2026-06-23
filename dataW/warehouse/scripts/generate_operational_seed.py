"""Generate Hive seed HQL from the active restaurant API export."""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen


OUTPUT_PATH = Path(os.getenv("WAREHOUSE_SEED_OUTPUT", "/workspace/warehouse/generated/operational_seed.hql"))
API_URL = os.getenv("WAREHOUSE_API_EXPORT_URL", "http://api/graph/export")
ZONES = ["Central", "Oeste", "Este", "Norte", "Sur"]


class SqlExpr:
    def __init__(self, value: str):
        self.value = value


def sql_string(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def sql_date(value: str) -> SqlExpr:
    return SqlExpr(f"CAST({sql_string(value)} AS DATE)")


def sql_timestamp(value: str) -> SqlExpr:
    return SqlExpr(f"CAST({sql_string(value)} AS TIMESTAMP)")


def sql_bool(value: bool) -> str:
    return "true" if value else "false"


def money(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def zone_for_id(value: int) -> str:
    return ZONES[(int(value) - 1) % len(ZONES)]


def fetch_export() -> dict:
    last_error = None
    for _ in range(30):
        try:
            with urlopen(API_URL, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"No se pudo consultar {API_URL}: {last_error}")


def complete_missing_order_items(payload: dict) -> None:
    order_items = payload.setdefault("order_items", [])
    menus_by_restaurant = {}
    for product in payload.get("products", []):
        menus_by_restaurant.setdefault(int(product["restaurant_id"]), []).append(product)

    existing_order_ids = {int(item["order_id"]) for item in order_items}
    generated_id = 900000
    for order in payload.get("orders", []):
        order_id = int(order["order_id"])
        if order_id in existing_order_ids:
            continue
        for product in menus_by_restaurant.get(int(order["restaurant_id"]), [])[:2]:
            generated_id += 1
            order_items.append(
                {
                    "order_item_id": generated_id,
                    "order_id": order_id,
                    "menu_id": int(product["menu_id"]),
                    "quantity": 1,
                    "price": money(product.get("price")),
                }
            )


def date_for_order(order_id: int) -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0) + timedelta(days=(int(order_id) - 1) % 120)


def time_row(dt: datetime) -> tuple:
    time_id = int(dt.strftime("%Y%m%d"))
    return (
        time_id,
        sql_date(dt.strftime("%Y-%m-%d")),
        dt.isoweekday(),
        dt.strftime("%A"),
        int(dt.strftime("%W")),
        dt.month,
        dt.strftime("%B"),
        math.ceil(dt.month / 3),
        dt.year,
        dt.weekday() >= 5,
        "N/A",
    )


def insert_values(table: str, rows: list[tuple]) -> str:
    if not rows:
        return f"-- No rows for {table}\n"
    rendered = []
    for row in rows:
        values = []
        for value in row:
            if isinstance(value, SqlExpr):
                values.append(value.value)
            elif isinstance(value, bool):
                values.append(sql_bool(value))
            elif isinstance(value, str):
                values.append(sql_string(value))
            elif value is None:
                values.append("NULL")
            else:
                values.append(str(value))
        rendered.append("(" + ", ".join(values) + ")")
    return f"INSERT INTO {table} VALUES\n" + ",\n".join(rendered) + ";\n"


def build_hql(payload: dict) -> str:
    complete_missing_order_items(payload)
    users = payload.get("users", [])
    restaurants = payload.get("restaurants", [])
    products = payload.get("products", [])
    orders = payload.get("orders", [])
    order_items = payload.get("order_items", [])

    if not users or not restaurants or not products or not orders:
        missing = [
            name
            for name, values in {
                "users": users,
                "restaurants": restaurants,
                "menus": products,
                "orders": orders,
            }.items()
            if not values
        ]
        raise RuntimeError(f"No hay datos operacionales suficientes para Hive. Faltan: {', '.join(missing)}")

    products_by_id = {int(product["menu_id"]): product for product in products}
    users_by_id = {int(user["user_id"]): user for user in users}
    order_by_id = {int(order["order_id"]): order for order in orders}
    items_by_order = {}
    for item in order_items:
        items_by_order.setdefault(int(item["order_id"]), []).append(item)

    time_rows_by_id = {}
    for order in orders:
        dt = date_for_order(int(order["order_id"]))
        time_rows_by_id[int(dt.strftime("%Y%m%d"))] = time_row(dt)

    customer_rows = []
    for user in users:
        user_id = int(user["user_id"])
        user_orders = [order for order in orders if int(order["client_id"]) == user_id]
        total_spent = 0.0
        for order in user_orders:
            total_spent += sum(money(item["price"]) * int(item["quantity"]) for item in items_by_order.get(int(order["order_id"]), []))
        customer_rows.append(
            (
                user_id,
                user["user_name"],
                user.get("role_name") or "cliente",
                sql_date("2026-01-01"),
                int(user_orders[0]["restaurant_id"]) if user_orders else 0,
                zone_for_id(user_id),
                min(len(user_orders), 5),
                round(total_spent, 2),
                len(user_orders),
                True,
            )
        )

    product_rows = []
    for product in products:
        price = money(product.get("price"))
        cost = round(price * 0.6, 2)
        product_rows.append(
            (
                int(product["menu_id"]),
                product["dish_name"],
                product.get("category") or "general",
                product.get("category") or "general",
                round(price, 2),
                cost,
                round(price - cost, 2),
                True,
                sql_date("2026-01-01"),
                sql_date("2026-01-01"),
            )
        )

    restaurant_rows = []
    for restaurant in restaurants:
        restaurant_id = int(restaurant["restaurant_id"])
        restaurant_rows.append(
            (
                restaurant_id,
                restaurant["restaurant_name"],
                zone_for_id(restaurant_id),
                zone_for_id(restaurant_id),
                50 + restaurant_id * 10,
                2020,
                f"2222-{restaurant_id:04d}",
                f"restaurante{restaurant_id}@local",
                "Activo" if int(restaurant.get("restaurant_status") or 1) else "Inactivo",
            )
        )

    status_rows = [
        (1, "Completed", "order", "Orden completada"),
        (2, "Cancelled", "order", "Orden cancelada"),
        (3, "Pending", "order", "Orden pendiente"),
        (4, "Confirmed", "reservation", "Reserva confirmada"),
        (5, "No Show", "reservation", "Cliente no asistio"),
        (6, "Cancelled", "reservation", "Reserva cancelada"),
    ]

    fact_rows = []
    for order in orders:
        order_id = int(order["order_id"])
        dt = date_for_order(order_id)
        order_time = dt + timedelta(hours=order_id % 8)
        for item in items_by_order.get(order_id, []):
            product = products_by_id.get(int(item["menu_id"]))
            if product is None:
                continue
            quantity = int(item["quantity"])
            unit_price = money(item["price"])
            total = round(quantity * unit_price, 2)
            tax = round(total * 0.13, 2)
            final = round(total + tax, 2)
            fact_rows.append(
                (
                    order_id,
                    int(order["client_id"]),
                    int(order["restaurant_id"]),
                    int(item["menu_id"]),
                    int(dt.strftime("%Y%m%d")),
                    1,
                    quantity,
                    round(unit_price, 2),
                    total,
                    0.0,
                    total,
                    tax,
                    final,
                    sql_timestamp(order_time.strftime("%Y-%m-%d %H:%M:%S")),
                    sql_timestamp((order_time + timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S")),
                )
            )

    hql = [
        "-- Generated from operational API /graph/export. Do not edit manually.",
        "TRUNCATE TABLE fact_orders;",
        "TRUNCATE TABLE fact_reservations;",
        "TRUNCATE TABLE dim_status;",
        "TRUNCATE TABLE dim_customer;",
        "TRUNCATE TABLE dim_product;",
        "TRUNCATE TABLE dim_restaurant;",
        "TRUNCATE TABLE dim_time;",
        "",
        insert_values("dim_time", sorted(time_rows_by_id.values(), key=lambda row: row[0])),
        insert_values("dim_customer", customer_rows),
        insert_values("dim_product", product_rows),
        insert_values("dim_restaurant", restaurant_rows),
        insert_values("dim_status", status_rows),
        insert_values("fact_orders", fact_rows),
        "-- No reservation source table is required for the three Superset dashboards.",
    ]
    return "\n".join(hql)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_export()
    hql = build_hql(payload)
    OUTPUT_PATH.write_text(hql, encoding="utf-8")
    print(f"[OK] Operational Hive seed generated at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
