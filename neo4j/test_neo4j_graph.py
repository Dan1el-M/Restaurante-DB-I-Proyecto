"""Validation script for Project 2 point 5: Neo4J graph analysis and routes."""

from __future__ import annotations

import os
import sys
from typing import Any

from neo4j import GraphDatabase


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def ok(message: str) -> None:
    print(f"[OK] {message}")


def error(message: str) -> None:
    print(f"[ERROR] {message}")


def scalar(session, query: str, **params: Any) -> Any:
    record = session.run(query, **params).single()
    return None if record is None else record[0]


def validate_count(session, description: str, query: str) -> bool:
    count = scalar(session, query)
    if count and count > 0:
        ok(description)
        return True
    error(f"{description} no cumple: resultado vacio o cero.")
    return False


def validate_query(session, description: str, query: str, **params: Any) -> bool:
    rows = list(session.run(query, **params))
    if rows:
        ok(description)
        for row in rows[:3]:
            print(f"     ejemplo: {dict(row)}")
        return True
    error(f"{description} no devolvio resultados.")
    return False


CO_PURCHASE_QUERY = """
MATCH (pedido:Pedido)-[:CONTIENE]->(p1:Producto)
MATCH (pedido)-[:CONTIENE]->(p2:Producto)
WHERE p1.id_producto < p2.id_producto
RETURN p1.nombre AS producto_1,
       p2.nombre AS producto_2,
       count(*) AS veces_comprados_juntos
ORDER BY veces_comprados_juntos DESC, producto_1, producto_2
LIMIT 5
"""

RECOMMENDERS_QUERY = """
MATCH (usuario:Usuario)-[:RECOMIENDA_A]->(recomendado:Usuario)
RETURN usuario.nombre AS usuario_recomendador,
       recomendado.nombre AS usuario_recomendado
ORDER BY usuario_recomendador, usuario_recomendado
LIMIT 10
"""

INFLUENTIAL_USERS_QUERY = """
MATCH (usuario:Usuario)
OPTIONAL MATCH (usuario)-[:RECOMIENDA_A]->(saliente:Usuario)
WITH usuario, count(saliente) AS recomendaciones_salientes
OPTIONAL MATCH (entrante:Usuario)-[:RECOMIENDA_A]->(usuario)
WITH usuario, recomendaciones_salientes, count(entrante) AS recomendaciones_entrantes
WITH usuario,
     recomendaciones_salientes,
     recomendaciones_entrantes,
     recomendaciones_salientes + recomendaciones_entrantes AS total_recomendaciones
WHERE total_recomendaciones > 0
RETURN usuario.nombre AS usuario,
       total_recomendaciones,
       CASE
         WHEN recomendaciones_salientes >= recomendaciones_entrantes THEN 'recomendador'
         ELSE 'referenciado'
       END AS tipo_influencia
ORDER BY total_recomendaciones DESC, usuario
"""

SHORTEST_PATH_QUERY = """
MATCH (origen:Ubicacion {id_ubicacion: $origen})
MATCH (destino:Ubicacion {id_ubicacion: $destino})
MATCH path = shortestPath((origen)-[:CONECTA_CON*..8]->(destino))
RETURN origen.nombre AS origen,
       destino.nombre AS destino,
       [n IN nodes(path) | n.nombre] AS ruta,
       reduce(total = 0.0, r IN relationships(path) | total + r.distancia_km) AS distancia_total,
       reduce(total = 0, r IN relationships(path) | total + r.tiempo_minutos) AS tiempo_estimado_total
"""

PRODUCTS_BY_ZONE_QUERY = """
MATCH (usuario:Usuario)-[:VIVE_EN]->(ubicacion:Ubicacion)
MATCH (usuario)-[:REALIZO]->(:Pedido)-[rel:CONTIENE]->(producto:Producto)
RETURN usuario.zona AS zona,
       producto.nombre AS producto,
       sum(rel.cantidad) AS cantidad_total
ORDER BY zona, cantidad_total DESC
LIMIT 10
"""

PRODUCT_RECOMMENDATION_QUERY = """
MATCH (pedido:Pedido)-[:CONTIENE]->(base:Producto {nombre: $producto})
MATCH (pedido)-[rel:CONTIENE]->(sugerido:Producto)
WHERE sugerido <> base
RETURN base.nombre AS producto_base,
       sugerido.nombre AS producto_recomendado,
       count(*) AS veces_juntos,
       sum(rel.cantidad) AS cantidad_observada
ORDER BY veces_juntos DESC, cantidad_observada DESC
LIMIT 5
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
                validations = [
                    ("Existen nodos Usuario.", "MATCH (n:Usuario) RETURN count(n)"),
                    ("Existen nodos Producto.", "MATCH (n:Producto) RETURN count(n)"),
                    ("Existen nodos Pedido.", "MATCH (n:Pedido) RETURN count(n)"),
                    ("Existen nodos Restaurante.", "MATCH (n:Restaurante) RETURN count(n)"),
                    ("Existen nodos Ubicacion.", "MATCH (n:Ubicacion) RETURN count(n)"),
                    ("Existen relaciones REALIZO.", "MATCH ()-[r:REALIZO]->() RETURN count(r)"),
                    ("Existen relaciones CONTIENE.", "MATCH ()-[r:CONTIENE]->() RETURN count(r)"),
                    ("Existen relaciones SALE_DE.", "MATCH ()-[r:SALE_DE]->() RETURN count(r)"),
                    ("Existen relaciones VIVE_EN.", "MATCH ()-[r:VIVE_EN]->() RETURN count(r)"),
                    ("Existen relaciones UBICADO_EN.", "MATCH ()-[r:UBICADO_EN]->() RETURN count(r)"),
                    ("Existen relaciones CONECTA_CON.", "MATCH ()-[r:CONECTA_CON]->() RETURN count(r)"),
                    ("Existen relaciones RECOMIENDA_A.", "MATCH ()-[r:RECOMIENDA_A]->() RETURN count(r)"),
                ]
                for description, query in validations:
                    if not validate_count(session, description, query):
                        failures += 1

                query_checks = [
                    ("Consulta de co-compra funciona.", CO_PURCHASE_QUERY, {}),
                    ("Consulta de usuarios recomendadores funciona.", RECOMMENDERS_QUERY, {}),
                    ("Consulta de usuarios influyentes funciona.", INFLUENTIAL_USERS_QUERY, {}),
                    (
                        "Consulta de caminos minimos funciona.",
                        SHORTEST_PATH_QUERY,
                        {"origen": "U_REST_CENTRAL", "destino": "U_OESTE"},
                    ),
                    ("Consulta de productos por zona funciona.", PRODUCTS_BY_ZONE_QUERY, {}),
                    (
                        "Consulta de recomendaciones por producto funciona.",
                        PRODUCT_RECOMMENDATION_QUERY,
                        {"producto": "Hamburguesa Clasica"},
                    ),
                ]
                for description, query, params in query_checks:
                    if not validate_query(session, description, query, **params):
                        failures += 1
    except Exception as exc:
        error(f"No se pudo validar Neo4J: {exc}")
        return 1

    if failures:
        error(f"Validacion finalizada con {failures} requisito(s) fallido(s).")
        return 1
    ok("Todos los requisitos del punto 5 se validaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
