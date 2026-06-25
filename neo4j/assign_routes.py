"""Assign delivery orders to drivers using Neo4J and nearest neighbor.

The script reads the graph created by load_graph.py, calculates the fastest
path between locations through CONECTA_CON relationships, assigns each pending
order to an available driver and persists ASIGNADO_A relationships for evidence.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Any

from neo4j import GraphDatabase


@dataclass
class Route:
    origin_id: str
    destination_id: str
    nodes: list[str]
    distance_km: float
    time_minutes: int


@dataclass
class Order:
    id_pedido: int
    estado: str
    restaurante: str
    cliente_destino: str
    origen_id: str
    destino_id: str


@dataclass
class Driver:
    id_repartidor: int
    nombre: str
    zona: str
    capacidad_pedidos: int
    ubicacion_actual_id: str
    ubicacion_actual_nombre: str
    assignments: list[dict[str, Any]] = field(default_factory=list)
    ubicacion_base_id: str = field(init=False)

    def __post_init__(self) -> None:
        self.ubicacion_base_id = self.ubicacion_actual_id

    @property
    def available_slots(self) -> int:
        return self.capacidad_pedidos - len(self.assignments)


def env(name: str, default: str) -> str:
    """Read an environment variable with a safe local default."""

    return os.getenv(name, default)


def fetch_drivers(session) -> list[Driver]:
    """Return available drivers with their current graph location."""

    query = """
    MATCH (r:Repartidor)-[:UBICADO_EN]->(loc:Ubicacion)
    WHERE r.estado = 'disponible'
    RETURN r.id_repartidor AS id_repartidor,
           r.nombre AS nombre,
           r.zona AS zona,
           r.capacidad_pedidos AS capacidad_pedidos,
           loc.id_ubicacion AS ubicacion_actual_id,
           loc.nombre AS ubicacion_actual_nombre
    ORDER BY r.id_repartidor
    """
    return [Driver(**dict(record)) for record in session.run(query)]


def fetch_orders(session) -> list[Order]:
    """Return deliverable orders with restaurant origin and customer location."""

    query = """
    MATCH (pedido:Pedido)-[:SALE_DE]->(restaurante:Restaurante)-[:UBICADO_EN]->(origen:Ubicacion)
    MATCH (pedido)-[:ENTREGAR_EN]->(destino:Ubicacion)
    WHERE pedido.estado <> 'Cancelled'
    RETURN pedido.id_pedido AS id_pedido,
           pedido.estado AS estado,
           restaurante.nombre AS restaurante,
           destino.nombre AS cliente_destino,
           origen.id_ubicacion AS origen_id,
           destino.id_ubicacion AS destino_id
    ORDER BY pedido.id_pedido
    """
    return [Order(**dict(record)) for record in session.run(query)]


def find_fastest_route(session, origin_id: str, destination_id: str, max_hops: int) -> Route | None:
    """Find the lowest-time path between two Ubicacion nodes in Neo4J."""

    if origin_id == destination_id:
        record = session.run(
            """
            MATCH (loc:Ubicacion {id_ubicacion: $origin_id})
            RETURN loc.nombre AS nombre
            """,
            origin_id=origin_id,
        ).single()
        name = record["nombre"] if record else origin_id
        return Route(origin_id, destination_id, [name], 0.0, 0)

    safe_max_hops = max(1, min(max_hops, 12))
    query = f"""
    MATCH (origen:Ubicacion {{id_ubicacion: $origin_id}})
    MATCH (destino:Ubicacion {{id_ubicacion: $destination_id}})
    MATCH path = (origen)-[:CONECTA_CON*1..{safe_max_hops}]->(destino)
    WITH path,
         reduce(total = 0.0, r IN relationships(path) | total + r.distancia_km) AS distancia_total,
         reduce(total = 0, r IN relationships(path) | total + r.tiempo_minutos) AS tiempo_total
    RETURN [n IN nodes(path) | n.nombre] AS ruta,
           distancia_total,
           tiempo_total
    ORDER BY tiempo_total ASC, distancia_total ASC
    LIMIT 1
    """
    record = session.run(query, origin_id=origin_id, destination_id=destination_id).single()
    if not record:
        return None
    return Route(
        origin_id=origin_id,
        destination_id=destination_id,
        nodes=record["ruta"],
        distance_km=float(record["distancia_total"]),
        time_minutes=int(record["tiempo_total"]),
    )


def choose_next_order(session, driver: Driver, orders: list[Order], max_hops: int) -> tuple[Order, Route, Route] | None:
    """Choose the nearest pending order from the driver's latest stop."""

    best: tuple[int, float, int, Order, Route, Route] | None = None
    for order in orders:
        if order.origen_id == driver.ubicacion_base_id:
            pickup_route = find_fastest_route(session, driver.ubicacion_actual_id, driver.ubicacion_actual_id, max_hops)
            delivery_route = find_fastest_route(session, driver.ubicacion_actual_id, order.destino_id, max_hops)
        else:
            pickup_route = find_fastest_route(session, driver.ubicacion_actual_id, order.origen_id, max_hops)
            delivery_route = find_fastest_route(session, order.origen_id, order.destino_id, max_hops)
        if pickup_route is None or delivery_route is None:
            continue
        total_time = pickup_route.time_minutes + delivery_route.time_minutes
        total_distance = pickup_route.distance_km + delivery_route.distance_km
        candidate = (total_time, total_distance, order.id_pedido, order, pickup_route, delivery_route)
        if best is None or candidate[:3] < best[:3]:
            best = candidate
    if best is None:
        return None
    return best[3], best[4], best[5]


def persist_assignment(session, driver: Driver, order: Order, sequence: int, pickup: Route, delivery: Route) -> None:
    """Persist an ASIGNADO_A relationship and update the in-memory route state."""

    full_route = pickup.nodes + delivery.nodes[1:]
    total_distance = round(pickup.distance_km + delivery.distance_km, 2)
    total_time = pickup.time_minutes + delivery.time_minutes
    query = """
    MATCH (r:Repartidor {id_repartidor: $id_repartidor})
    MATCH (p:Pedido {id_pedido: $id_pedido})
    MERGE (r)-[rel:ASIGNADO_A]->(p)
    SET rel.orden_entrega = $sequence,
        rel.distancia_total_km = $total_distance,
        rel.tiempo_total_minutos = $total_time,
        rel.ruta = $route,
        rel.heuristica = 'vecino_mas_cercano'
    """
    session.run(
        query,
        id_repartidor=driver.id_repartidor,
        id_pedido=order.id_pedido,
        sequence=sequence,
        total_distance=total_distance,
        total_time=total_time,
        route=full_route,
    )
    driver.assignments.append(
        {
            "pedido": order,
            "pickup": pickup,
            "delivery": delivery,
            "ruta": full_route,
            "distancia_total_km": total_distance,
            "tiempo_total_minutos": total_time,
        }
    )
    driver.ubicacion_actual_id = order.destino_id
    driver.ubicacion_actual_nombre = order.cliente_destino


def clear_previous_assignments(session) -> None:
    """Remove previous point 6 assignments so the demo is reproducible."""

    session.run("MATCH ()-[rel:ASIGNADO_A]->() DELETE rel")


def print_courier_routes(drivers: list[Driver]) -> None:
    """Print route details and totals grouped by driver."""

    print("\nAsignaciones optimizadas por vecino mas cercano")
    print("=" * 58)
    for courier in drivers:
        print(f"\nRepartidor: {courier.nombre} | Zona: {courier.zona}")
        if not courier.assignments:
            print("  Sin pedidos asignados.")
            continue
        assigned_order_ids = []
        total_distance = 0.0
        total_minutes = 0
        full_route: list[str] = []
        for index, item in enumerate(courier.assignments, start=1):
            order = item["pedido"]
            assigned_order_ids.append(order.id_pedido)
            total_distance += float(item["distancia_total_km"])
            total_minutes += int(item["tiempo_total_minutos"])
            if not full_route:
                full_route.extend(item["ruta"])
            else:
                full_route.extend(item["ruta"][1:])
            print(f"  {index}. Pedido {order.id_pedido} ({order.restaurante} -> {order.cliente_destino})")
            print(f"     Ruta: {' -> '.join(item['ruta'])}")
            print(f"     Distancia: {item['distancia_total_km']} km")
            print(f"     Tiempo estimado: {item['tiempo_total_minutos']} min")
        print(f"  Pedidos asignados: {assigned_order_ids}")
        print(f"  Ruta consolidada: {' -> '.join(full_route)}")
        print(f"  Distancia total: {round(total_distance, 2)} km")
        print(f"  Tiempo total estimado: {total_minutes} min")


def assign_routes(max_hops: int, clean: bool) -> int:
    """Run the point 6 assignment flow against a live Neo4J database."""

    uri = env("NEO4J_URI", "bolt://localhost:7687")
    user = env("NEO4J_USER", "neo4j")
    password = env("NEO4J_PASSWORD", "restaurant123")
    database = env("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver:
        driver.verify_connectivity()
        with driver.session(database=database) as session:
            if clean:
                clear_previous_assignments(session)

            drivers = fetch_drivers(session)
            orders = fetch_orders(session)
            if not drivers:
                print("[ERROR] No hay repartidores disponibles. Ejecute primero neo4j/load_graph.py.")
                return 1
            if not orders:
                print("[ERROR] No hay pedidos entregables. Ejecute primero neo4j/load_graph.py.")
                return 1

            print("[OK] Se cargaron repartidores disponibles.")
            print("[OK] Se cargaron pedidos pendientes con ubicacion.")
            print(f"     Repartidores disponibles: {len(drivers)}")
            print(f"     Pedidos a asignar: {len(orders)}")
            unassigned = orders[:]

            while unassigned and any(d.available_slots > 0 for d in drivers):
                progress = False
                for courier in drivers:
                    if not unassigned or courier.available_slots <= 0:
                        continue
                    selected = choose_next_order(session, courier, unassigned, max_hops)
                    if selected is None:
                        continue
                    order, pickup_route, delivery_route = selected
                    persist_assignment(
                        session,
                        courier,
                        order,
                        sequence=len(courier.assignments) + 1,
                        pickup=pickup_route,
                        delivery=delivery_route,
                    )
                    unassigned.remove(order)
                    progress = True
                if not progress:
                    break

            if unassigned:
                print("\n[ERROR] Pedidos sin asignar:", ", ".join(str(order.id_pedido) for order in unassigned))
                return 1

            print("[OK] Se calculo la distancia entre ubicaciones.")
            print("[OK] Se aplico algoritmo de vecino mas cercano.")
            print("[OK] Se asignaron pedidos a repartidores.")
            print("[OK] Se generaron rutas optimizadas.")
            print("[OK] Se calculo distancia total por repartidor.")
            print("[OK] Se calculo tiempo estimado por ruta.")
            print_courier_routes(drivers)
            print("\n[OK] Todos los pedidos entregables fueron asignados.")
            print("[OK] Relaciones ASIGNADO_A creadas en Neo4J.")
            print("[OK] Punto 6 validado correctamente.")
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Asigna rutas de entrega usando vecino mas cercano.")
    parser.add_argument("--max-hops", type=int, default=8, help="Maximo de saltos al buscar rutas.")
    parser.add_argument("--no-clean", action="store_true", help="No borrar asignaciones anteriores.")
    args = parser.parse_args()
    return assign_routes(max_hops=args.max_hops, clean=not args.no_clean)


if __name__ == "__main__":
    sys.exit(main())
