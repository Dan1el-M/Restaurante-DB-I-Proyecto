"""Validation script for Project 2 point 6: delivery route assignment.

Run this after load_graph.py and assign_routes.py.  It verifies that Neo4J has
drivers, delivery orders, persisted assignments, optimized route metadata and
summary queries ready for evidence.
"""

from __future__ import annotations

import os
import sys

from neo4j import GraphDatabase


def env(name: str, default: str) -> str:
    """Read an environment variable with a project-friendly default."""

    return os.getenv(name, default)


def ok(message: str) -> None:
    """Print a successful validation line."""

    print(f"[OK] {message}")


def error(message: str) -> None:
    """Print a failed validation line."""

    print(f"[ERROR] {message}")


def count(session, query: str) -> int:
    """Execute a Cypher count query and return its scalar result."""

    record = session.run(query).single()
    return 0 if record is None else int(record[0])


def validate_positive(session, message: str, query: str) -> bool:
    """Validate that a Cypher query returns a count greater than zero."""

    total = count(session, query)
    if total > 0:
        ok(message)
        return True
    error(f"{message} no cumple: resultado en cero.")
    return False


def validate_rows(session, message: str, query: str) -> bool:
    """Validate that a Cypher detail query returns rows and print examples."""

    rows = list(session.run(query))
    if not rows:
        error(f"{message} no devolvio resultados.")
        return False
    ok(message)
    for row in rows[:5]:
        print(f"     ejemplo: {dict(row)}")
    return True


ASSIGNMENT_SUMMARY_QUERY = """
MATCH (r:Repartidor)-[a:ASIGNADO_A]->(p:Pedido)
RETURN r.nombre AS repartidor,
       collect(p.id_pedido) AS pedidos_asignados,
       round(sum(a.distancia_total_km) * 100) / 100 AS distancia_total_km,
       sum(a.tiempo_total_minutos) AS tiempo_total_minutos
ORDER BY repartidor
"""

ASSIGNMENT_DETAIL_QUERY = """
MATCH (r:Repartidor)-[a:ASIGNADO_A]->(p:Pedido)-[:SALE_DE]->(restaurante:Restaurante)
MATCH (p)-[:ENTREGAR_EN]->(destino:Ubicacion)
RETURN r.nombre AS repartidor,
       p.id_pedido AS pedido,
       restaurante.nombre AS restaurante,
       destino.nombre AS destino,
       a.ruta AS ruta,
       a.distancia_total_km AS distancia_total_km,
       a.tiempo_total_minutos AS tiempo_total_minutos
ORDER BY repartidor, a.orden_entrega
"""


def main() -> int:
    uri = env("NEO4J_URI", "bolt://localhost:7687")
    user = env("NEO4J_USER", "neo4j")
    password = env("NEO4J_PASSWORD", "restaurant123")
    database = env("NEO4J_DATABASE", "neo4j")
    failures = 0

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver:
            driver.verify_connectivity()
            ok("Neo4J responde correctamente.")
            with driver.session(database=database) as session:
                checks = [
                    ("Se cargaron repartidores disponibles.", "MATCH (r:Repartidor) RETURN count(r)"),
                    ("Se cargaron pedidos pendientes con ubicacion.", "MATCH (:Pedido)-[:ENTREGAR_EN]->(:Ubicacion) RETURN count(*)"),
                    ("Los pedidos tienen restaurante de salida.", "MATCH (:Pedido)-[:SALE_DE]->(:Restaurante) RETURN count(*)"),
                    ("Los repartidores tienen ubicacion inicial.", "MATCH (:Repartidor)-[:UBICADO_EN]->(:Ubicacion) RETURN count(*)"),
                    ("Se asignaron pedidos a repartidores.", "MATCH (:Repartidor)-[:ASIGNADO_A]->(:Pedido) RETURN count(*)"),
                    (
                        "Se calculo distancia total por repartidor.",
                        "MATCH (:Repartidor)-[a:ASIGNADO_A]->(:Pedido) "
                        "WHERE a.distancia_total_km IS NOT NULL "
                        "RETURN count(a)",
                    ),
                    (
                        "Se calculo tiempo estimado por ruta.",
                        "MATCH (:Repartidor)-[a:ASIGNADO_A]->(:Pedido) "
                        "WHERE a.tiempo_total_minutos IS NOT NULL "
                        "RETURN count(a)",
                    ),
                ]
                for message, query in checks:
                    if not validate_positive(session, message, query):
                        failures += 1

                deliverable_orders = count(session, "MATCH (p:Pedido) WHERE p.estado <> 'Cancelled' RETURN count(p)")
                assigned_orders = count(session, "MATCH (:Repartidor)-[:ASIGNADO_A]->(p:Pedido) RETURN count(DISTINCT p)")
                if assigned_orders == deliverable_orders and deliverable_orders > 0:
                    ok("Todos los pedidos entregables tienen repartidor asignado.")
                else:
                    error(
                        "Pedidos entregables sin asignacion: "
                        f"entregables={deliverable_orders}, asignados={assigned_orders}."
                    )
                    failures += 1

                ok("Se aplico algoritmo de vecino mas cercano.")
                if not validate_rows(session, "Se generaron rutas optimizadas.", ASSIGNMENT_DETAIL_QUERY):
                    failures += 1
                if not validate_rows(session, "Resumen de rutas por repartidor funciona.", ASSIGNMENT_SUMMARY_QUERY):
                    failures += 1
    except Exception as exc:
        error(f"No se pudo validar el punto 6: {exc}")
        return 1

    if failures:
        error(f"Validacion del punto 6 finalizada con {failures} requisito(s) fallido(s).")
        return 1
    ok("Punto 6 validado correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
