from __future__ import annotations

import os
import time

from common import docker_client, get_container


def find_spark_mount_source() -> str:
    spark_master = get_container(os.getenv("SPARK_MASTER_CONTAINER", "restaurant-spark-master"))
    for mount in spark_master.attrs.get("Mounts", []):
        if mount.get("Destination") == "/workspace/spark":
            return mount["Source"]
    raise RuntimeError("Could not find host mount for /workspace/spark in restaurant-spark-master")


def find_network_name() -> str:
    spark_master = get_container(os.getenv("SPARK_MASTER_CONTAINER", "restaurant-spark-master"))
    networks = spark_master.attrs.get("NetworkSettings", {}).get("Networks", {})
    for network_name in networks:
        if "restaurant-network" in network_name:
            return network_name
    if networks:
        return next(iter(networks))
    raise RuntimeError("Could not detect Docker network from restaurant-spark-master")


def main() -> None:
    """
    Ejecuta el job PySpark del punto 2 en un contenedor one-shot.

    Airflow no reemplaza Spark: lo orquesta creando un contenedor compatible con
    el servicio existente `spark-analytics`, conectado al mismo master/worker.
    """
    client = docker_client()
    image = os.getenv("SPARK_IMAGE", "apache/spark:3.5.5-scala2.12-java17-python3-ubuntu")
    network_name = find_network_name()
    spark_source = find_spark_mount_source()
    container_name = f"restaurant-airflow-spark-analytics-{int(time.time())}"
    command = [
        "/opt/spark/bin/spark-submit",
        "--master",
        os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077"),
        "/workspace/spark/jobs/analytics_job.py",
    ]

    print("==> run_spark_transformations")
    print(f"Image: {image}")
    print(f"Network: {network_name}")
    print(f"Spark mount source: {spark_source}")
    print(f"Command: {' '.join(command)}")

    container = client.containers.run(
        image=image,
        name=container_name,
        command=command,
        detach=True,
        network=network_name,
        volumes={spark_source: {"bind": "/workspace/spark", "mode": "rw"}},
        environment={
            "SPARK_MASTER_URL": os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077"),
            "SPARK_SCALE_FACTOR": os.getenv("SPARK_SCALE_FACTOR", "1000"),
            "SPARK_SHUFFLE_PARTITIONS": os.getenv("SPARK_SHUFFLE_PARTITIONS", "4"),
        },
    )

    try:
        for line in container.logs(stream=True, follow=True):
            print(line.decode("utf-8", errors="replace").rstrip())
        result = container.wait()
        exit_code = result.get("StatusCode", 1)
        if exit_code != 0:
            raise RuntimeError(f"Spark analytics container failed with exit code {exit_code}")
    finally:
        container.remove(force=True)

    print("==> SPARK ORCHESTRATION COMPLETED")


if __name__ == "__main__":
    main()
