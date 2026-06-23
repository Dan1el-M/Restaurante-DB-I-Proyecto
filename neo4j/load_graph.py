"""Load the restaurant graph from the operational database into Neo4J."""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse, urlunparse

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience for container usage
    load_dotenv = None

from neo4j import GraphDatabase
from pymongo import MongoClient
import requests
from sqlalchemy import create_engine, text


if load_dotenv is not None:
    load_dotenv()


ZONES = ["Central", "Oeste", "Este", "Norte", "Sur"]
BASE_COORDS = {
    "Central": (9.8644, -83.9194),
    "Oeste": (9.9300, -84.0900),
    "Este": (9.9000, -83.8500),
    "Norte": (9.9800, -83.9300),
    "Sur": (9.8200, -83.9300),
}


@dataclass
class GraphData:
    users: list[dict[str, Any]]
    restaurants: list[dict[str, Any]]
    products: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    order_items: list[dict[str, Any]]
    roles: list[dict[str, Any]]


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def localize_docker_url(url: str) -> str:
    """Allow host execution with .env values that point to Docker DNS names."""
    if env("NEO4J_USE_DOCKER_DNS", "false").lower() in {"1", "true", "yes"}:
        return url
    replacements = {
        "postgres": "localhost",
        "mongos": "localhost",
    }
    parsed = urlparse(url)
    host = parsed.hostname
    if host not in replacements:
        return url
    netloc = replacements[host]
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        netloc = f"{auth}@{netloc}"
    return urlunparse(parsed._replace(netloc=netloc))


def as_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def money(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return 0.0
    return float(value)


def zone_for_id(value: int) -> str:
    return ZONES[(int(value) - 1) % len(ZONES)]


def location_id(prefix: str, value: int) -> str:
    return f"{prefix}_{int(value)}"


def location_for(zone: str, value: int, kind: str) -> tuple[float, float]:
    base_lat, base_lng = BASE_COORDS.get(zone, BASE_COORDS["Central"])
    offset = (int(value) % 11) * 0.003
    if kind == "cliente":
        return base_lat + offset, base_lng - offset
    return base_lat - offset / 2, base_lng + offset / 2


def distance_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1 = math.radians(float(a["latitud"]))
    lng1 = math.radians(float(a["longitud"]))
    lat2 = math.radians(float(b["latitud"]))
    lng2 = math.radians(float(b["longitud"]))
    d_lat = lat2 - lat1
    d_lng = lng2 - lng1
    hav = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    return round(6371 * 2 * math.atan2(math.sqrt(hav), math.sqrt(1 - hav)), 2)


def create_constraints(session) -> None:
    statements = [
        "CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (n:Usuario) REQUIRE n.id_usuario IS UNIQUE",
        "CREATE CONSTRAINT producto_id IF NOT EXISTS FOR (n:Producto) REQUIRE n.id_producto IS UNIQUE",
        "CREATE CONSTRAINT pedido_id IF NOT EXISTS FOR (n:Pedido) REQUIRE n.id_pedido IS UNIQUE",
        "CREATE CONSTRAINT restaurante_id IF NOT EXISTS FOR (n:Restaurante) REQUIRE n.id_restaurante IS UNIQUE",
        "CREATE CONSTRAINT ubicacion_id IF NOT EXISTS FOR (n:Ubicacion) REQUIRE n.id_ubicacion IS UNIQUE",
        "CREATE CONSTRAINT repartidor_id IF NOT EXISTS FOR (n:Repartidor) REQUIRE n.id_repartidor IS UNIQUE",
        "CREATE INDEX usuario_zona IF NOT EXISTS FOR (n:Usuario) ON (n.zona)",
        "CREATE INDEX producto_nombre IF NOT EXISTS FOR (n:Producto) ON (n.nombre)",
        "CREATE INDEX producto_categoria IF NOT EXISTS FOR (n:Producto) ON (n.categoria)",
        "CREATE INDEX ubicacion_nombre IF NOT EXISTS FOR (n:Ubicacion) ON (n.nombre)",
        "CREATE INDEX repartidor_zona IF NOT EXISTS FOR (n:Repartidor) ON (n.zona)",
    ]
    for statement in statements:
        session.run(statement)


def clear_graph(session) -> None:
    session.run("MATCH (n) DETACH DELETE n")


def load_from_postgres() -> GraphData:
    postgres_url = env(
        "GRAPH_POSTGRES_URL",
        env("POSTGRES_URL", "postgresql+psycopg2://postgres:postgres123@localhost:5432/restaurant_postgres_db"),
    )
    engine = create_engine(localize_docker_url(postgres_url))
    with engine.connect() as conn:
        roles = [as_dict(row) for row in conn.execute(text("SELECT role_id, role_name FROM roles"))]
        users = [
            as_dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT u.user_id, u.user_name, u.keycloak_id, u.role_id, r.role_name
                    FROM users u
                    LEFT JOIN roles r ON r.role_id = u.role_id
                    ORDER BY u.user_id
                    """
                )
            )
        ]
        restaurants = [
            as_dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT restaurant_id, restaurant_name, admin_id, restaurant_status
                    FROM restaurants
                    ORDER BY restaurant_id
                    """
                )
            )
        ]
        products = [
            as_dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT menu_id, dish_name, category, price, restaurant_id
                    FROM menus
                    ORDER BY menu_id
                    """
                )
            )
        ]
        orders = [
            as_dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT o.order_id,
                           o.table_id,
                           o.client_id,
                           o.order_type,
                           o.restaurant_id,
                           COALESCE(SUM(oi.quantity * oi.price), 0) AS total
                    FROM orders o
                    LEFT JOIN order_items oi ON oi.order_id = o.order_id
                    GROUP BY o.order_id, o.table_id, o.client_id, o.order_type, o.restaurant_id
                    ORDER BY o.order_id
                    """
                )
            )
        ]
        order_items = [
            as_dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT order_item_id, order_id, menu_id, quantity, price
                    FROM order_items
                    ORDER BY order_item_id
                    """
                )
            )
        ]
    return GraphData(
        users=users,
        restaurants=restaurants,
        products=products,
        orders=orders,
        order_items=order_items,
        roles=roles,
    )


def load_from_mongo() -> GraphData:
    mongo_url = env("GRAPH_MONGO_URL", env("MONGO_URL", "mongodb://localhost:27017/restaurant_mongo_db"))
    mongo_db_name = env("MONGO_DB", "restaurant_mongo_db")
    client = MongoClient(localize_docker_url(mongo_url))
    db = client[mongo_db_name]
    roles = list(db.roles.find({}, {"_id": 0}))
    role_by_id = {role.get("role_id"): role.get("role_name") for role in roles}
    users = []
    for user in db.users.find({}, {"_id": 0}).sort("user_id", 1):
        user["role_name"] = role_by_id.get(user.get("role_id"))
        users.append(user)
    restaurants = list(db.restaurants.find({}, {"_id": 0}).sort("restaurant_id", 1))
    products = list(db.menus.find({}, {"_id": 0}).sort("menu_id", 1))
    order_items = list(db.order_items.find({}, {"_id": 0}).sort("order_item_id", 1))
    totals: dict[int, float] = {}
    for item in order_items:
        totals[int(item["order_id"])] = totals.get(int(item["order_id"]), 0.0) + money(item["price"]) * int(item["quantity"])
    orders = []
    for order in db.orders.find({}, {"_id": 0}).sort("order_id", 1):
        order["total"] = totals.get(int(order["order_id"]), 0.0)
        orders.append(order)
    return GraphData(users=users, restaurants=restaurants, products=products, orders=orders, order_items=order_items, roles=roles)


def load_from_api() -> GraphData:
    api_url = env("GRAPH_API_URL", env("API_URL", "http://localhost:8000").rstrip("/") + "/graph/export")
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return GraphData(
        users=payload.get("users", []),
        restaurants=payload.get("restaurants", []),
        products=payload.get("products", []),
        orders=payload.get("orders", []),
        order_items=payload.get("order_items", []),
        roles=payload.get("roles", []),
    )


def fetch_graph_data(source: str) -> GraphData:
    if source == "postgres":
        return load_from_postgres()
    if source == "mongo":
        return load_from_mongo()
    if source == "api":
        return load_from_api()
    raise ValueError("GRAPH_SOURCE debe ser 'postgres', 'mongo' o 'api'")


def validate_source_data(data: GraphData) -> None:
    missing = []
    if not data.users:
        missing.append("users")
    if not data.restaurants:
        missing.append("restaurants")
    if not data.products:
        missing.append("menus")
    if not data.orders:
        missing.append("orders")
    if missing:
        raise RuntimeError(
            "La base de datos no tiene datos suficientes para construir el grafo. "
            f"Faltan registros en: {', '.join(missing)}. "
            "Neo4J necesita al menos usuarios, restaurantes, menus y pedidos existentes."
        )


def complete_missing_order_items(data: GraphData) -> None:
    menus_by_restaurant: dict[int, list[dict[str, Any]]] = {}
    for product in data.products:
        menus_by_restaurant.setdefault(int(product["restaurant_id"]), []).append(product)

    existing_order_ids = {int(item["order_id"]) for item in data.order_items}
    generated_id = 900000
    for order in data.orders:
        order_id = int(order["order_id"])
        if order_id in existing_order_ids:
            continue
        restaurant_menus = menus_by_restaurant.get(int(order["restaurant_id"]), [])
        if not restaurant_menus:
            continue
        for product in restaurant_menus[:2]:
            generated_id += 1
            data.order_items.append(
                {
                    "order_item_id": generated_id,
                    "order_id": order_id,
                    "menu_id": int(product["menu_id"]),
                    "quantity": 1,
                    "price": money(product.get("price")),
                    "source": "derived_from_order_restaurant_menu",
                }
            )
        order["total"] = sum(
            money(item["price"]) * int(item["quantity"])
            for item in data.order_items
            if int(item["order_id"]) == order_id
        )


def build_locations(data: GraphData) -> list[dict[str, Any]]:
    locations = []
    for user in data.users:
        zone = zone_for_id(int(user["user_id"]))
        lat, lng = location_for(zone, int(user["user_id"]), "cliente")
        locations.append(
            {
                "id_ubicacion": location_id("USER", int(user["user_id"])),
                "nombre": f"Cliente {user['user_name']}",
                "latitud": lat,
                "longitud": lng,
                "tipo": "cliente",
                "zona": zone,
            }
        )
    for restaurant in data.restaurants:
        zone = zone_for_id(int(restaurant["restaurant_id"]))
        lat, lng = location_for(zone, int(restaurant["restaurant_id"]), "restaurante")
        locations.append(
            {
                "id_ubicacion": location_id("REST", int(restaurant["restaurant_id"])),
                "nombre": f"Restaurante {restaurant['restaurant_name']}",
                "latitud": lat,
                "longitud": lng,
                "tipo": "restaurante",
                "zona": zone,
            }
        )
    return locations


def build_edges(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges = []
    for idx, origin in enumerate(locations):
        ranked = sorted(
            (target for target in locations if target["id_ubicacion"] != origin["id_ubicacion"]),
            key=lambda target: distance_km(origin, target),
        )
        for target in ranked[:3]:
            distance = max(distance_km(origin, target), 0.1)
            edges.append(
                {
                    "origen": origin["id_ubicacion"],
                    "destino": target["id_ubicacion"],
                    "distancia_km": distance,
                    "tiempo_minutos": max(1, math.ceil(distance / 25 * 60)),
                }
            )
        if idx + 1 < len(locations):
            target = locations[idx + 1]
            distance = max(distance_km(origin, target), 0.1)
            edges.append(
                {
                    "origen": origin["id_ubicacion"],
                    "destino": target["id_ubicacion"],
                    "distancia_km": distance,
                    "tiempo_minutos": max(1, math.ceil(distance / 25 * 60)),
                }
            )
    unique = {}
    for edge in edges:
        key = tuple(sorted([edge["origen"], edge["destino"]]))
        unique[key] = edge
    return list(unique.values())


def build_repartidores(data: GraphData) -> list[dict[str, Any]]:
    admins = [user for user in data.users if str(user.get("role_name", "")).lower() == "admin"]
    source_users = admins or data.users[: max(1, min(3, len(data.users)))]
    repartidores = []
    for index, user in enumerate(source_users[:3], start=1):
        restaurant = data.restaurants[(index - 1) % len(data.restaurants)]
        repartidores.append(
            {
                "id_repartidor": int(user["user_id"]),
                "nombre": f"Repartidor {user['user_name']}",
                "zona": zone_for_id(int(restaurant["restaurant_id"])),
                "estado": "disponible",
                "capacidad_pedidos": 4,
                "id_ubicacion_actual": location_id("REST", int(restaurant["restaurant_id"])),
            }
        )
    return repartidores


def load_ubicaciones(session, rows: list[dict[str, Any]]) -> None:
    session.run(
        """
        UNWIND $rows AS row
        MERGE (u:Ubicacion {id_ubicacion: row.id_ubicacion})
        SET u.nombre = row.nombre,
            u.latitud = toFloat(row.latitud),
            u.longitud = toFloat(row.longitud),
            u.tipo = row.tipo,
            u.zona = row.zona
        """,
        rows=rows,
    )


def load_usuarios(session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["zona"] = zone_for_id(int(row["user_id"]))
        row["id_ubicacion"] = location_id("USER", int(row["user_id"]))
        row["correo"] = row.get("keycloak_id") or f"{row['user_name']}@local"
        row["tipo_usuario"] = row.get("role_name") or "usuario"
    session.run(
        """
        UNWIND $rows AS row
        MATCH (loc:Ubicacion {id_ubicacion: row.id_ubicacion})
        MERGE (u:Usuario {id_usuario: toInteger(row.user_id)})
        SET u.nombre = row.user_name,
            u.correo = row.correo,
            u.zona = row.zona,
            u.tipo_usuario = row.tipo_usuario
        MERGE (u)-[:VIVE_EN]->(loc)
        """,
        rows=rows,
    )


def load_productos(session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["precio"] = money(row.get("price"))
    session.run(
        """
        UNWIND $rows AS row
        MERGE (p:Producto {id_producto: toInteger(row.menu_id)})
        SET p.nombre = row.dish_name,
            p.categoria = row.category,
            p.precio = toFloat(row.precio),
            p.id_restaurante = toInteger(row.restaurant_id)
        """,
        rows=rows,
    )


def load_restaurantes(session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["zona"] = zone_for_id(int(row["restaurant_id"]))
        row["id_ubicacion"] = location_id("REST", int(row["restaurant_id"]))
    session.run(
        """
        UNWIND $rows AS row
        MATCH (loc:Ubicacion {id_ubicacion: row.id_ubicacion})
        MERGE (r:Restaurante {id_restaurante: toInteger(row.restaurant_id)})
        SET r.nombre = row.restaurant_name,
            r.zona = row.zona,
            r.estado = toInteger(row.restaurant_status)
        MERGE (r)-[:UBICADO_EN]->(loc)
        """,
        rows=rows,
    )


def load_pedidos(session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["estado"] = "Completed"
        row["fecha"] = "2026-01-01"
        row["total"] = money(row.get("total"))
        row["id_destino"] = location_id("USER", int(row["client_id"]))
    session.run(
        """
        UNWIND $rows AS row
        MATCH (u:Usuario {id_usuario: toInteger(row.client_id)})
        MATCH (r:Restaurante {id_restaurante: toInteger(row.restaurant_id)})
        MATCH (destino:Ubicacion {id_ubicacion: row.id_destino})
        MERGE (p:Pedido {id_pedido: toInteger(row.order_id)})
        SET p.fecha = date(row.fecha),
            p.estado = row.estado,
            p.tipo = row.order_type,
            p.total = toFloat(row.total)
        MERGE (u)-[:REALIZO]->(p)
        MERGE (p)-[:SALE_DE]->(r)
        MERGE (p)-[:ENTREGAR_EN]->(destino)
        """,
        rows=rows,
    )


def load_pedido_productos(session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["subtotal"] = money(row.get("price")) * int(row["quantity"])
    session.run(
        """
        UNWIND $rows AS row
        MATCH (pedido:Pedido {id_pedido: toInteger(row.order_id)})
        MATCH (producto:Producto {id_producto: toInteger(row.menu_id)})
        MERGE (pedido)-[rel:CONTIENE]->(producto)
        SET rel.cantidad = toInteger(row.quantity),
            rel.subtotal = toFloat(row.subtotal)
        """,
        rows=rows,
    )


def load_conexiones(session, rows: list[dict[str, Any]]) -> None:
    session.run(
        """
        UNWIND $rows AS row
        MATCH (origen:Ubicacion {id_ubicacion: row.origen})
        MATCH (destino:Ubicacion {id_ubicacion: row.destino})
        MERGE (origen)-[ida:CONECTA_CON]->(destino)
        SET ida.distancia_km = toFloat(row.distancia_km),
            ida.tiempo_minutos = toInteger(row.tiempo_minutos)
        MERGE (destino)-[vuelta:CONECTA_CON]->(origen)
        SET vuelta.distancia_km = toFloat(row.distancia_km),
            vuelta.tiempo_minutos = toInteger(row.tiempo_minutos)
        """,
        rows=rows,
    )


def load_recomendaciones(session) -> None:
    session.run(
        """
        MATCH (u1:Usuario)-[:REALIZO]->(:Pedido)-[:CONTIENE]->(p:Producto)
        MATCH (u2:Usuario)-[:REALIZO]->(:Pedido)-[:CONTIENE]->(p)
        WHERE u1.id_usuario < u2.id_usuario
        WITH u1, u2, count(DISTINCT p) AS productos_en_comun
        WHERE productos_en_comun > 0
        MERGE (u1)-[r:RECOMIENDA_A]->(u2)
        SET r.cantidad_recomendaciones = productos_en_comun,
            r.origen = 'compras_reales'
        """
    )
    session.run(
        """
        MATCH (u1:Usuario)-[:REALIZO]->(:Pedido)-[:SALE_DE]->(r:Restaurante)
        MATCH (u2:Usuario)-[:REALIZO]->(:Pedido)-[:SALE_DE]->(r)
        WHERE u1.id_usuario < u2.id_usuario
        WITH u1, u2, count(DISTINCT r) AS restaurantes_en_comun
        WHERE restaurantes_en_comun > 0
        MERGE (u1)-[rel:RECOMIENDA_A]->(u2)
        SET rel.cantidad_recomendaciones = coalesce(rel.cantidad_recomendaciones, 0) + restaurantes_en_comun,
            rel.origen = 'actividad_real_compartida'
        """
    )


def load_repartidores(session, rows: list[dict[str, Any]]) -> None:
    session.run(
        """
        UNWIND $rows AS row
        MATCH (loc:Ubicacion {id_ubicacion: row.id_ubicacion_actual})
        MERGE (r:Repartidor {id_repartidor: toInteger(row.id_repartidor)})
        SET r.nombre = row.nombre,
            r.zona = row.zona,
            r.estado = row.estado,
            r.capacidad_pedidos = toInteger(row.capacidad_pedidos)
        MERGE (r)-[:UBICADO_EN]->(loc)
        """,
        rows=rows,
    )


def print_counts(session) -> None:
    labels = ["Usuario", "Producto", "Pedido", "Restaurante", "Ubicacion", "Repartidor"]
    relations = ["REALIZO", "CONTIENE", "SALE_DE", "ENTREGAR_EN", "VIVE_EN", "UBICADO_EN", "CONECTA_CON", "RECOMIENDA_A"]
    for label in labels:
        count = session.run(f"MATCH (n:{label}) RETURN count(n) AS total").single()["total"]
        print(f"[OK] {label}: {count} nodos")
    for rel_type in relations:
        count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS total").single()["total"]
        print(f"[OK] {rel_type}: {count} relaciones")


def load_graph(source: str, clean: bool) -> None:
    data = fetch_graph_data(source)
    validate_source_data(data)
    complete_missing_order_items(data)
    locations = build_locations(data)
    edges = build_edges(locations)
    repartidores = build_repartidores(data)

    uri = env("NEO4J_URI", "bolt://localhost:7687")
    user = env("NEO4J_USER", "neo4j")
    password = env("NEO4J_PASSWORD", "restaurant123")

    print(f"Fuente operacional: {source}")
    print(f"Conectando a Neo4J en {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver:
        driver.verify_connectivity()
        with driver.session(database=env("NEO4J_DATABASE", "neo4j")) as session:
            if clean:
                print("Limpiando grafo anterior...")
                clear_graph(session)
            print("Creando constraints e indices...")
            create_constraints(session)
            print("Cargando ubicaciones desde usuarios/restaurantes reales...")
            load_ubicaciones(session, locations)
            print("Cargando usuarios...")
            load_usuarios(session, data.users)
            print("Cargando productos...")
            load_productos(session, data.products)
            print("Cargando restaurantes...")
            load_restaurantes(session, data.restaurants)
            print("Cargando pedidos...")
            load_pedidos(session, data.orders)
            print("Cargando productos por pedido...")
            load_pedido_productos(session, data.order_items)
            print("Cargando conexiones entre ubicaciones...")
            load_conexiones(session, edges)
            print("Creando recomendaciones desde compras reales compartidas...")
            load_recomendaciones(session)
            print("Cargando repartidores desde usuarios operativos...")
            load_repartidores(session, repartidores)
            print("\nResumen de carga:")
            print_counts(session)
    print("\n[OK] Grafo Neo4J cargado desde la base de datos correctamente.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga Neo4J desde PostgreSQL o MongoDB del proyecto.")
    parser.add_argument(
        "--source",
        choices=["postgres", "mongo", "api"],
        default=env("GRAPH_SOURCE", env("DATABASE_ENGINE", "postgres")).split("#", 1)[0].strip().lower(),
        help="Base operacional de origen.",
    )
    parser.add_argument("--no-clean", action="store_true", help="No borrar el grafo antes de cargar.")
    args = parser.parse_args()
    load_graph(args.source, clean=not args.no_clean)


if __name__ == "__main__":
    main()
