from __future__ import annotations

import os
import socket
import subprocess
from pathlib import Path
from typing import Iterable

import docker


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def docker_client():
    return docker.from_env()


def get_container(name: str):
    return docker_client().containers.get(name)


def project_state_dir() -> Path:
    path = Path(os.getenv("AIRFLOW_POINT4_STATE_DIR", "/opt/airflow/state"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_tcp(host: str, port: int, timeout: float = 5.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def exec_in_container(container_name: str, command: Iterable[str], stdin: str | None = None) -> str:
    container = get_container(container_name)
    if container.status != "running":
        raise RuntimeError(f"Container {container_name} is not running; current status={container.status}")

    result = container.exec_run(list(command), stdin=stdin, demux=True)
    stdout = (result.output[0] or b"").decode("utf-8", errors="replace") if result.output else ""
    stderr = (result.output[1] or b"").decode("utf-8", errors="replace") if result.output else ""
    output = stdout + stderr
    print(output)

    if result.exit_code != 0:
        raise RuntimeError(
            f"Command failed in {container_name} with exit code {result.exit_code}: {' '.join(command)}"
        )

    return output


def run_local(command: Iterable[str], env: dict | None = None) -> str:
    print(f"Running local command: {' '.join(command)}")
    completed = subprocess.run(
        list(command),
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    print(output)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")
    return output
