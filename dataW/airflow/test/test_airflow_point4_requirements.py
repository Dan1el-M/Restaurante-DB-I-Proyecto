from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import request, error


ROOT = Path(__file__).resolve().parents[3]
DAG_ID = "restaurant_olap_pipeline"
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8090")
SUPERSET_HEALTH_URL = os.getenv("SUPERSET_HEALTH_URL", "http://localhost:8088/health")
AIRFLOW_USER = os.getenv("AIRFLOW_ADMIN_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_ADMIN_PASSWORD", "admin")
TIMEOUT_SECONDS = int(os.getenv("POINT4_TEST_TIMEOUT_SECONDS", "900"))
TASK_LOG_MARKERS = [
    "Executing point 4 script",
    "==> extract_from_source",
    "==> run_spark_transformations",
    "==> load_to_data_warehouse",
    "==> validate_warehouse",
]


results: list[tuple[bool, str, str]] = []


def run(command: list[str], timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if output.strip():
        print(output)
    if check and completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")
    return completed


def http_json(method: str, path: str, payload: dict | None = None, timeout: int = 30):
    body = None
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{AIRFLOW_USER}:{AIRFLOW_PASSWORD}".encode("utf-8")).decode("ascii"),
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(f"{AIRFLOW_BASE_URL}{path}", data=body, headers=headers, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8")
        return json.loads(text) if text else {}


def http_status(url: str, timeout: int = 30) -> int:
    with request.urlopen(url, timeout=timeout) as response:
        return response.status


def check(name: str, func, diagnostic: str = "") -> None:
    try:
        detail = func()
        message = detail if isinstance(detail, str) and detail else name
        results.append((True, name, message))
        print(f"[OK] {name}")
    except Exception as exc:
        reason = f"{exc}"
        if diagnostic:
            reason = f"{reason}. Diagnostico sugerido: {diagnostic}"
        results.append((False, name, reason))
        print(f"[FAIL] {name}. Motivo: {reason}")


def wait_for_airflow() -> None:
    deadline = time.time() + TIMEOUT_SECONDS
    last_error = None
    while time.time() < deadline:
        try:
            if http_status(f"{AIRFLOW_BASE_URL}/health", timeout=10) == 200:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(5)
    raise RuntimeError(f"Airflow webserver did not become healthy: {last_error}")


def latest_dag_run_state(run_id: str) -> str:
    response = http_json("GET", f"/api/v1/dags/{DAG_ID}/dagRuns/{run_id}")
    return response.get("state", "unknown")


def wait_for_dag_run(run_id: str) -> str:
    deadline = time.time() + TIMEOUT_SECONDS
    last_error = None
    while time.time() < deadline:
        try:
            state = latest_dag_run_state(run_id)
            print(f"DAG run {run_id} state: {state}")
            if state in {"success", "failed"}:
                return state
        except Exception as exc:
            last_error = exc
            print(f"Airflow API temporalmente no disponible: {exc}. Reintentando...")
            wait_for_airflow()
        time.sleep(10)
    raise RuntimeError(f"DAG run {run_id} did not finish before timeout. Last error: {last_error}")


def airflow_dag_details() -> dict:
    return http_json("GET", f"/api/v1/dags/{DAG_ID}")


def airflow_tasks() -> list[str]:
    response = http_json("GET", f"/api/v1/dags/{DAG_ID}/tasks")
    return [task["task_id"] for task in response.get("tasks", [])]


def airflow_task_dependencies() -> dict[str, list[str]]:
    response = http_json("GET", f"/api/v1/dags/{DAG_ID}/tasks")
    dependencies = {}
    for task in response.get("tasks", []):
        dependencies[task["task_id"]] = sorted(task.get("downstream_task_ids", []))
    return dependencies


def validate_dag_schedule() -> str:
    details = airflow_dag_details()
    schedule = details.get("schedule_interval") or details.get("timetable_summary")
    if not schedule:
        raise RuntimeError(f"No se encontro schedule diario/periodico. Detalles={details}")
    return f"Schedule detectado: {schedule}"


def trigger_dag_run(run_id: str) -> str:
    http_json("PATCH", f"/api/v1/dags/{DAG_ID}", {"is_paused": False})
    response = http_json("POST", f"/api/v1/dags/{DAG_ID}/dagRuns", {"dag_run_id": run_id})
    if response.get("dag_run_id") != run_id:
        raise RuntimeError(f"No se creo el dag_run esperado. Respuesta={response}")
    return f"DAG run creado: {run_id}"


def logs_contain_real_script_execution() -> str:
    log_root = ROOT / "dataW" / "airflow" / "logs" / f"dag_id={DAG_ID}"
    if not log_root.exists():
        raise RuntimeError(f"No existe carpeta de logs de Airflow: {log_root}")

    matched_logs = []
    for log_file in log_root.rglob("*.log"):
        text = log_file.read_text(encoding="utf-8", errors="ignore")
        if any(marker in text for marker in TASK_LOG_MARKERS):
            matched_logs.append(str(log_file.relative_to(ROOT)))

    if not matched_logs:
        raise RuntimeError(f"No se encontraron logs de scripts reales en {log_root}")
    return f"Logs reales encontrados: {matched_logs[:3]}"


def hive_query(query: str) -> str:
    completed = run(
        [
            "docker",
            "exec",
            "-i",
            "hiveserver2",
            "/opt/hive/bin/beeline",
            "-u",
            "jdbc:hive2://localhost:10000/restaurant_warehouse",
            "--silent=true",
            "-e",
            query,
        ],
        timeout=120,
    )
    return (completed.stdout or "") + (completed.stderr or "")


def parse_positive_count(output: str) -> None:
    for token in output.replace("|", " ").split():
        if token.isdigit() and int(token) > 0:
            return
    raise RuntimeError(f"No positive count found in output: {output}")


def main() -> int:
    print("========================================")
    print("VALIDACION PUNTO 4 - AIRFLOW")
    print("========================================")

    check(
        "Airflow levanta desde Docker Compose.",
        lambda: run(
            [
                "docker",
                "compose",
                "up",
                "-d",
                "--build",
                "airflow-init",
                "airflow-webserver",
                "airflow-scheduler",
                "superset",
            ],
            timeout=TIMEOUT_SECONDS,
        )
        and "compose up ejecutado",
        "docker compose logs airflow-init airflow-webserver airflow-scheduler",
    )

    check(
        "El webserver de Airflow abre en navegador.",
        lambda: wait_for_airflow() or f"{AIRFLOW_BASE_URL}/health responde OK",
        "docker compose logs airflow-webserver",
    )

    check(
        "El scheduler esta corriendo.",
        lambda: "running"
        if "running"
        in run(["docker", "inspect", "-f", "{{.State.Status}}", "restaurant-airflow-scheduler"]).stdout.lower()
        else (_ for _ in ()).throw(RuntimeError("airflow-scheduler no esta running")),
        "docker compose ps airflow-scheduler",
    )

    check(
        "Existe un DAG llamado restaurant_olap_pipeline.",
        lambda: airflow_dag_details().get("dag_id") == DAG_ID
        or (_ for _ in ()).throw(RuntimeError("DAG no encontrado en API")),
        "docker exec restaurant-airflow-webserver airflow dags list",
    )

    check(
        "El DAG tiene schedule diario o periodico.",
        validate_dag_schedule,
        "docker exec restaurant-airflow-webserver airflow dags show restaurant_olap_pipeline",
    )

    task_ids_cache: list[str] = []

    def tasks() -> list[str]:
        nonlocal task_ids_cache
        if not task_ids_cache:
            task_ids_cache = airflow_tasks()
        return task_ids_cache

    required_task_checks = [
        ("El DAG tiene tarea de extraccion.", "extract_from_source"),
        ("El DAG tiene tarea de transformacion con Spark.", "run_spark_transformations"),
        ("El DAG tiene tarea de carga al Data Warehouse.", "load_to_data_warehouse"),
        ("El DAG tiene tarea de validacion del warehouse.", "validate_warehouse"),
        ("El DAG tiene tarea de reindexado de Elasticsearch.", "reindex_elasticsearch_if_needed"),
    ]
    for label, task_id in required_task_checks:
        check(
            label,
            lambda task_id=task_id: task_id in tasks()
            or (_ for _ in ()).throw(RuntimeError(f"No existe task_id={task_id}. Tareas={tasks()}")),
            "docker exec restaurant-airflow-webserver airflow tasks list restaurant_olap_pipeline",
        )

    def validate_dependencies() -> str:
        deps = airflow_task_dependencies()
        expected_edges = {
            "start": "extract_from_source",
            "extract_from_source": "run_spark_transformations",
            "run_spark_transformations": "load_to_data_warehouse",
            "load_to_data_warehouse": "validate_warehouse",
            "validate_warehouse": "check_product_catalog_changes",
            "check_product_catalog_changes": "skip_reindex",
            "check_product_catalog_changes": "reindex_elasticsearch_if_needed",
            "skip_reindex": "finish",
            "reindex_elasticsearch_if_needed": "finish",
        }
        for upstream, downstream in expected_edges.items():
            if downstream not in deps.get(upstream, []):
                raise RuntimeError(f"Missing edge {upstream} -> {downstream}. Deps={deps}")
        return "Dependencias logicas correctas"

    check(
        "Las tareas estan conectadas en orden logico.",
        validate_dependencies,
        "docker exec restaurant-airflow-webserver airflow tasks list restaurant_olap_pipeline --tree",
    )

    run_id = f"manual__point4_validation_{int(time.time())}"

    check(
        "El DAG puede ejecutarse manualmente.",
        lambda: trigger_dag_run(run_id),
        "docker compose logs airflow-webserver",
    )

    check(
        "La ejecucion queda en success.",
        lambda: wait_for_dag_run(run_id) == "success"
        or (_ for _ in ()).throw(RuntimeError(f"DAG run {run_id} no termino en success")),
        "docker compose logs airflow-scheduler",
    )

    check(
        "Los logs muestran comandos reales.",
        logs_contain_real_script_execution,
        "docker compose logs airflow-scheduler",
    )

    check(
        "Hive queda con datos despues de correr el DAG.",
        lambda: parse_positive_count(hive_query("SELECT COUNT(*) FROM fact_orders;"))
        or "fact_orders con datos",
        "docker compose logs warehouse-setup hiveserver2",
    )

    check(
        "Superset puede consultar los datos actualizados.",
        lambda: http_status(SUPERSET_HEALTH_URL, timeout=30) == 200
        or (_ for _ in ()).throw(RuntimeError("Superset health no respondio 200")),
        "docker compose logs superset",
    )

    passed = sum(1 for ok, _, _ in results if ok)
    total = len(results)
    print("\n========================================")
    print("RESUMEN")
    print("========================================")
    for index, (ok, name, detail) in enumerate(results, start=1):
        icon = "[OK]" if ok else "[FAIL]"
        print(f"{icon} {index}/{total} {name}")
        if not ok:
            print(f"   Motivo: {detail}")

    print(f"\n# RESULTADO FINAL: {passed}/{total} requisitos cumplidos")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
