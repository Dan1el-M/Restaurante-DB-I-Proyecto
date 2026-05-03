import os
import time

import pytest
import requests


def _wait_ok(url: str, timeout_s: int = 120) -> None:
    """Espera a que una URL retorne 200 OK. Reintenta cada 2s hasta timeout."""
    deadline = time.time() + timeout_s
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                return
        except Exception as exc:  # pragma: no cover
            last_exc = exc
        time.sleep(2)
    if last_exc:
        raise last_exc
    raise AssertionError(f"No OK response from {url} within {timeout_s}s")


def _wait_any_ok(urls: list[str], timeout_s: int = 120) -> str:
    """Espera a que ALGUNA URL en lista retorne 200 OK. Retorna URL que respondió."""
    last_exc: Exception | None = None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for url in urls:
            try:
                r = requests.get(url, timeout=5)
                if r.ok:
                    return url
            except Exception as exc:  # pragma: no cover
                last_exc = exc
        time.sleep(2)
    if last_exc:
        raise last_exc
    raise AssertionError(f"No OK response from any of: {urls} within {timeout_s}s")


@pytest.mark.integration
def test_api_and_keycloak_are_reachable():
    """Valida que Keycloak y API están levantados y responden correctamente."""
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8001").rstrip("/")

    # Espera a Keycloak (intenta health/ready, health/live o health)
    _wait_any_ok(
        [
            f"{keycloak_base}/health/ready",
            f"{keycloak_base}/health/live",
            f"{keycloak_base}/health",
        ],
        timeout_s=180,
    )
    # Espera a API
    _wait_ok(f"{api_base}/health")

    # Valida que /ping responde correctamente
    assert requests.get(f"{api_base}/ping", timeout=5).json()["message"] == "pong"
