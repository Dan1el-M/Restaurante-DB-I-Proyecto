"""Tests unitarios para main.py y endpoints públicos"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app.api_main import app


class TestPublicEndpoints:
    """Pruebas para endpoints públicos"""
    
    def test_ping_endpoint(self):
        """Endpoint /ping"""
        client = TestClient(app)
        response = client.get("/ping")
        
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}
    
    def test_health_endpoint(self):
        """Endpoint /health"""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_root_endpoint(self):
        """Endpoint raíz /"""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "API funcionando"
        assert data["version"] == "1.0.0"


class TestAppMetadata:
    """Pruebas para metadata de la aplicación"""
    
    def test_app_title(self):
        """Título de la aplicación"""
        assert app.title == "Restaurante API"
    
    def test_app_version(self):
        """Versión de la aplicación"""
        assert app.version == "1.0.0"
    
    def test_app_description(self):
        """Descripción de la aplicación"""
        assert "restaurantes" in app.description.lower()

