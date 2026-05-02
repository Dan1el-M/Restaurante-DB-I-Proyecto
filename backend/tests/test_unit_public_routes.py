import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_public_routes_smoke():
    """Valida que rutas públicas (/ping, /health, /) están disponibles y funcionales."""
    from backend.app.main import app

    client = TestClient(app)

    assert client.get("/ping").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
    root = client.get("/").json()
    assert root["message"] == "API funcionando"

