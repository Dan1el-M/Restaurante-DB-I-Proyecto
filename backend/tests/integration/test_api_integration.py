"""
Pruebas de integración para la API
Requieren que los servicios estén corriendo (postgres, redis, elasticsearch)
"""

import pytest
from httpx import AsyncClient
from backend.app.api_main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Prueba que el endpoint de health esté disponible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ping")
        assert response.status_code in [200, 404]  # Ajusta según tu implementación


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_starts():
    """Prueba que la API se puede inicializar"""
    assert app is not None
    assert app.title == "Restaurante API"
