from __future__ import annotations

from common import exec_in_container, wait_for_container


HIVE_CONTAINER = "hiveserver2"
WAREHOUSE_JDBC = "jdbc:hive2://localhost:10000/restaurant_warehouse"
DEFAULT_JDBC = "jdbc:hive2://localhost:10000/default"


def run_beeline(args: list[str]) -> str:
    return exec_in_container(HIVE_CONTAINER, ["/opt/hive/bin/beeline", *args])


def table_count(table_name: str) -> int:
    output = run_beeline(["-u", WAREHOUSE_JDBC, "--silent=true", "--showHeader=false", "-e", f"SELECT COUNT(*) FROM {table_name};"])
    for token in output.replace("|", " ").split():
        if token.isdigit():
            return int(token)
    return 0


def main() -> None:
    """
    Crea/actualiza el Data Warehouse en Hive de manera idempotente.

    El schema y las vistas usan CREATE IF NOT EXISTS / CREATE VIEW luego de
    DROP VIEW. El seed solo se ejecuta cuando fact_orders esta vacia para evitar
    duplicados innecesarios en corridas diarias de Airflow.
    """
    print("==> load_to_data_warehouse")
    wait_for_container(HIVE_CONTAINER, tcp_host="hiveserver2", tcp_port=10000)
    run_beeline(["-u", DEFAULT_JDBC, "-e", "CREATE DATABASE IF NOT EXISTS restaurant_warehouse;"])
    run_beeline(["-u", WAREHOUSE_JDBC, "-f", "/workspace/warehouse/schemas/schema_star.sql"])

    current_orders = table_count("fact_orders")
    print(f"Current fact_orders rows before seed: {current_orders}")
    if current_orders == 0:
        print("fact_orders is empty; loading warehouse seed data.")
        run_beeline(["-u", WAREHOUSE_JDBC, "-f", "/workspace/warehouse/tests/seed_warehouse.hql"])
    else:
        print("fact_orders already has data; skipping seed to keep load idempotent.")

    run_beeline(["-u", WAREHOUSE_JDBC, "-f", "/workspace/warehouse/schemas/hive_olap_views.sql"])
    print("==> DATA WAREHOUSE LOAD COMPLETED")


if __name__ == "__main__":
    main()
