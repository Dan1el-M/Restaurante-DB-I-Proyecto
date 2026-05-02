from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_app() -> FastAPI:
    """Crea app FastAPI minimalista con endpoints de health check."""
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"message": "pong"}

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


def test_health_endpoint_returns_ok():
    """Valida que GET /health retorna 200 con status='ok'."""
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ping_endpoint_returns_pong():
    """Valida que GET /ping retorna 200 con message='pong'."""
    client = TestClient(create_app())
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
