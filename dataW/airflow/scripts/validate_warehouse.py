from __future__ import annotations

from common import exec_in_container


HIVE_CONTAINER = "hiveserver2"
WAREHOUSE_JDBC = "jdbc:hive2://localhost:10000/restaurant_warehouse"

REQUIRED_OBJECTS = [
    "fact_orders",
    "fact_reservations",
    "cubo_ingresos_mes_categoria",
    "cubo_actividad_clientes_zona",
    "cubo_ordenes_completadas_canceladas",
]


def beeline(query: str) -> str:
    return exec_in_container(
        HIVE_CONTAINER,
        ["/opt/hive/bin/beeline", "-u", WAREHOUSE_JDBC, "--silent=true", "-e", query],
    )


def parse_first_int(output: str) -> int:
    for token in output.replace("|", " ").split():
        if token.isdigit():
            return int(token)
    raise RuntimeError(f"Could not parse integer from Hive output: {output}")


def assert_count_positive(table_name: str) -> None:
    output = beeline(f"SELECT COUNT(*) FROM {table_name};")
    count = parse_first_int(output)
    print(f"{table_name}: {count} rows")
    if count <= 0:
        raise RuntimeError(f"{table_name} has no rows")


def main() -> None:
    print("==> validate_warehouse")
    tables_output = beeline("SHOW TABLES;")
    lower_output = tables_output.lower()

    for object_name in REQUIRED_OBJECTS:
        if object_name.lower() not in lower_output:
            raise RuntimeError(f"Required Hive object not found: {object_name}")
        print(f"Found Hive object: {object_name}")

    assert_count_positive("fact_orders")
    assert_count_positive("fact_reservations")
    assert_count_positive("cubo_ingresos_mes_categoria")
    assert_count_positive("cubo_actividad_clientes_zona")
    assert_count_positive("cubo_ordenes_completadas_canceladas")

    sample = beeline("SELECT * FROM cubo_ingresos_mes_categoria LIMIT 5;")
    if "ingresos_totales" not in sample.lower() and "plato" not in sample.lower():
        raise RuntimeError("Sample query from cubo_ingresos_mes_categoria did not return expected content")

    print("==> WAREHOUSE VALIDATION COMPLETED")


if __name__ == "__main__":
    main()
