from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator


SCRIPTS_DIR = Path(os.getenv("AIRFLOW_POINT4_SCRIPTS_DIR", "/opt/airflow/scripts"))
POINT6_SCRIPT = Path(os.getenv("AIRFLOW_POINT6_SCRIPT", "/opt/airflow/neo4j/delivery_assignment.py"))


def run_script(script_name: str) -> str:
    script_path = SCRIPTS_DIR / script_name
    command = ["python", str(script_path)]
    print(f"Executing point 4 script: {' '.join(command)}")
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    output = (completed.stdout or "") + (completed.stderr or "")
    print(output)
    if completed.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {completed.returncode}")
    return output


def extract_from_source_callable() -> None:
    run_script("extract_from_source.py")


def run_spark_transformations_callable() -> None:
    run_script("run_spark_transformations.py")


def load_to_data_warehouse_callable() -> None:
    run_script("load_to_data_warehouse.py")


def validate_warehouse_callable() -> None:
    run_script("validate_warehouse.py")


def validate_delivery_routes_callable() -> None:
    """Optionally run the standalone point 6 route assignment validation."""

    enabled = os.getenv("ENABLE_DELIVERY_ROUTE_VALIDATION", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        print("Skipping optional point 6 route validation. Set ENABLE_DELIVERY_ROUTE_VALIDATION=true to run it.")
        return
    command = ["python", str(POINT6_SCRIPT)]
    print(f"Executing point 6 script: {' '.join(command)}")
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    output = (completed.stdout or "") + (completed.stderr or "")
    print(output)
    if completed.returncode != 0:
        raise RuntimeError(f"Point 6 route validation failed with exit code {completed.returncode}")


def check_product_catalog_changes_callable() -> str:
    output = run_script("check_catalog_changes.py")
    if "CATALOG_CHANGED=true" in output:
        return "reindex_elasticsearch_if_needed"
    return "skip_reindex"


def reindex_elasticsearch_callable() -> None:
    run_script("reindex_elasticsearch.py")


default_args = {
    "owner": "restaurant-data-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="restaurant_olap_pipeline",
    description="Orquesta extraccion, Spark, carga Hive, validacion OLAP y reindexado Search del proyecto Restaurante.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["olap", "airflow", "spark", "hive", "restaurant"],
) as dag:
    start = EmptyOperator(task_id="start")

    extract_from_source = PythonOperator(
        task_id="extract_from_source",
        python_callable=extract_from_source_callable,
    )

    run_spark_transformations = PythonOperator(
        task_id="run_spark_transformations",
        python_callable=run_spark_transformations_callable,
    )

    load_to_data_warehouse = PythonOperator(
        task_id="load_to_data_warehouse",
        python_callable=load_to_data_warehouse_callable,
    )

    validate_warehouse = PythonOperator(
        task_id="validate_warehouse",
        python_callable=validate_warehouse_callable,
    )

    validate_delivery_routes = PythonOperator(
        task_id="validate_delivery_routes_optional",
        python_callable=validate_delivery_routes_callable,
    )

    check_product_catalog_changes = BranchPythonOperator(
        task_id="check_product_catalog_changes",
        python_callable=check_product_catalog_changes_callable,
    )

    reindex_elasticsearch_if_needed = PythonOperator(
        task_id="reindex_elasticsearch_if_needed",
        python_callable=reindex_elasticsearch_callable,
    )

    skip_reindex = EmptyOperator(task_id="skip_reindex")

    finish = EmptyOperator(task_id="finish", trigger_rule="none_failed_min_one_success")

    (
        start
        >> extract_from_source
        >> run_spark_transformations
        >> load_to_data_warehouse
        >> validate_warehouse
        >> validate_delivery_routes
        >> check_product_catalog_changes
        >> [reindex_elasticsearch_if_needed, skip_reindex]
        >> finish
    )
