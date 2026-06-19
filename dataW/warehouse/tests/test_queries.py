#!/usr/bin/env python3
"""
Genera consultas de prueba para validar el Data Warehouse OLAP.

Uso:
    python dataW/warehouse/tests/test_queries.py
    hive -f dataW/warehouse/tests/test_queries.hql
"""

from pathlib import Path


QUERIES = [
    (
        "Top 5 productos por categoria",
        """
SELECT
    product_name,
    category,
    veces_vendido,
    cantidad_total,
    ingresos_producto,
    ranking_categoria
FROM cubo_bestsellers_productos
WHERE ranking_categoria <= 5
ORDER BY category, ranking_categoria;
""",
    ),
    (
        "Ingresos por mes y categoria",
        """
SELECT
    year,
    month,
    month_name,
    category,
    total_ordenes,
    ingresos_totales,
    promedio_orden
FROM cubo_ingresos_mes_categoria
ORDER BY year DESC, month DESC, ingresos_totales DESC
LIMIT 20;
""",
    ),
    (
        "Actividad por zona geografica",
        """
SELECT
    geographic_zone,
    restaurant_location,
    total_clientes_unicos,
    total_ordenes,
    total_reservaciones,
    ingresos_zona,
    ticket_promedio,
    tamano_promedio_grupo
FROM cubo_actividad_clientes_zona
ORDER BY ingresos_zona DESC
LIMIT 20;
""",
    ),
    (
        "Horarios pico",
        """
SELECT
    day_name,
    month_name,
    hora,
    category,
    ordenes_por_hora,
    items_vendidos,
    ingresos_hora
FROM cubo_tendencias_horarios_pico
ORDER BY ordenes_por_hora DESC
LIMIT 20;
""",
    ),
    (
        "Frecuencia por cliente",
        """
SELECT
    customer_id,
    customer_name,
    customer_type,
    loyalty_level,
    total_ordenes_cliente,
    total_reservaciones_cliente,
    gasto_total_cliente,
    dias_desde_primera_compra
FROM cubo_lealtad_clientes
ORDER BY total_ordenes_cliente DESC, total_reservaciones_cliente DESC
LIMIT 20;
""",
    ),
    (
        "Rendimiento por restaurante",
        """
SELECT
    restaurant_name,
    location,
    geographic_zone,
    total_ordenes,
    total_reservaciones,
    ingresos_totales,
    ticket_promedio,
    clientes_unicos,
    porcentaje_no_show
FROM cubo_rendimiento_restaurantes
ORDER BY ingresos_totales DESC
LIMIT 20;
""",
    ),
    (
        "Ocupacion de mesas",
        """
SELECT
    restaurant_name,
    month_name,
    day_name,
    reservaciones_realizadas,
    mesas_ocupadas,
    porcentaje_ocupacion,
    tamano_promedio_grupo,
    minutos_promedio_ocupacion
FROM cubo_ocupacion_mesas
ORDER BY porcentaje_ocupacion DESC
LIMIT 20;
""",
    ),
    (
        "Rentabilidad mensual",
        """
SELECT
    restaurant_name,
    year,
    month,
    month_name,
    ingresos_brutos,
    costo_productos,
    ganancia_bruta,
    margen_porcentaje,
    total_ordenes
FROM cubo_rentabilidad
ORDER BY year DESC, month DESC, ganancia_bruta DESC
LIMIT 20;
""",
    ),
]


def build_hql() -> str:
    sections = [
        "-- =====================================================",
        "-- Data Warehouse OLAP - Consultas de prueba",
        "-- =====================================================",
        "",
    ]

    for title, query in QUERIES:
        sections.append(f"-- {title}")
        sections.append(query.strip())
        sections.append("")

    return "\n".join(sections)


def main() -> None:
    output_path = Path(__file__).with_name("test_queries.hql")
    output_path.write_text(build_hql(), encoding="utf-8")
    print(f"Script generado: {output_path}")
    print(f"Ejecutar con: hive -f {output_path}")


if __name__ == "__main__":
    main()
