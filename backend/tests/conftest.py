import pytest
import os
import sys
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


@pytest.fixture
def mock_dao():
    """Mock DAO para pruebas"""
    dao = Mock()
    dao.get_user = Mock()
    dao.get_user_by_username = Mock()
    dao.get_user_by_keycloak_id = Mock()
    dao.create_user = Mock()
    dao.update_user = Mock()
    dao.delete_user = Mock()
    dao.list_users = Mock()
    
    dao.get_restaurant = Mock()
    dao.list_restaurants = Mock()
    dao.create_restaurant = Mock()
    dao.update_restaurant = Mock()
    dao.delete_restaurant = Mock()
    
    dao.get_role_by_name = Mock()
    dao.get_role = Mock()
    
    return dao


@pytest.fixture
def mock_payload_admin():
    """Payload de token Keycloak con rol admin"""
    return {
        "sub": "user-123",
        "username": "admin_user",
        "realm_access": {
            "roles": ["admin"]
        }
    }


@pytest.fixture
def mock_payload_user():
    """Payload de token Keycloak con rol client"""
    return {
        "sub": "user-456",
        "username": "regular_user",
        "realm_access": {
            "roles": ["client"]
        }
    }


@pytest.fixture
def mock_payload_no_roles():
    """Payload de token Keycloak sin roles"""
    return {
        "sub": "user-789",
        "username": "no_roles_user",
        "realm_access": {
            "roles": []
        }
    }


@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    from backend.app.api_main import app
    return TestClient(app)
