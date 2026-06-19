"""Tests unitarios para routers - users"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.routers import users
from backend.database import get_dao


def make_users_app(mock_dao, token_payload):
    app = FastAPI()
    app.include_router(users.router)
    app.dependency_overrides[get_dao] = lambda: mock_dao
    app.dependency_overrides[users.get_current_user] = lambda: token_payload
    return app


def test_get_me_success(mock_dao, mock_payload_admin):
    """Obtener usuario autenticado exitosamente"""
    user = {
        "user_id": 1,
        "user_name": "admin_user",
        "role_id": 1,
        "keycloak_id": "user-123"
    }
    mock_dao.get_user_by_keycloak_id.return_value = user
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    response = client.get("/users/me")
    
    assert response.status_code == 200
    assert response.json()["user_id"] == 1
    mock_dao.get_user_by_keycloak_id.assert_called_once_with("user-123")


def test_get_me_no_sub_claim(mock_dao):
    """Token sin claim 'sub'"""
    payload = {"realm_access": {"roles": ["admin"]}}
    mock_dao.get_user_by_keycloak_id.return_value = None
    
    client = TestClient(make_users_app(mock_dao, payload))
    response = client.get("/users/me")
    
    assert response.status_code == 401


def test_get_me_user_not_found(mock_dao, mock_payload_admin):
    """Usuario no encontrado en BD"""
    mock_dao.get_user_by_keycloak_id.return_value = None
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    response = client.get("/users/me")
    
    assert response.status_code == 404


def test_update_user_success(mock_dao, mock_payload_admin):
    """Actualizar usuario exitosamente"""
    user = {
        "user_id": 1,
        "user_name": "admin_user",
        "role_id": 1,
        "keycloak_id": "user-123"
    }
    mock_dao.get_user.return_value = user
    mock_dao.get_user_by_username.return_value = None
    mock_dao.update_user.return_value = {
        **user,
        "user_name": "admin_user_updated"
    }
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    with patch("backend.app.routers.users.update_user_in_keycloak"):
        response = client.put("/users/1", json={"user_name": "admin_user_updated"})
    
    assert response.status_code == 200


def test_update_user_forbidden_different_user(mock_dao, mock_payload_user):
    """Actualizar usuario diferente sin ser admin"""
    user = {
        "user_id": 2,
        "user_name": "other_user",
        "role_id": 2,
        "keycloak_id": "other-keycloak-user"
    }
    mock_dao.get_user.return_value = user
    
    client = TestClient(make_users_app(mock_dao, mock_payload_user))
    response = client.put("/users/2", json={"user_name": "new_name"})
    
    assert response.status_code == 403


def test_update_user_cannot_change_role(mock_dao, mock_payload_admin):
    """No se puede cambiar rol desde este endpoint"""
    user = {
        "user_id": 1,
        "user_name": "admin_user",
        "role_id": 1,
        "keycloak_id": "user-123"
    }
    mock_dao.get_user.return_value = user
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    response = client.put("/users/1", json={"role_id": 2})
    
    assert response.status_code == 403


def test_update_user_duplicate_username(mock_dao, mock_payload_admin):
    """Username ya está en uso"""
    user = {
        "user_id": 1,
        "user_name": "admin_user",
        "role_id": 1,
        "keycloak_id": "user-123"
    }
    other_user = {
        "user_id": 2,
        "user_name": "new_name",
        "role_id": 2,
        "keycloak_id": "user-456"
    }
    mock_dao.get_user.return_value = user
    mock_dao.get_user_by_username.return_value = other_user
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    response = client.put("/users/1", json={"user_name": "new_name"})
    
    assert response.status_code == 400


def test_delete_user_success(mock_dao, mock_payload_admin):
    """Eliminar usuario exitosamente"""
    user = {
        "user_id": 1,
        "user_name": "admin_user",
        "role_id": 1,
        "keycloak_id": "user-123"
    }
    mock_dao.get_user.return_value = user
    mock_dao.delete_user.return_value = True
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    with patch("backend.app.routers.users.delete_user_from_keycloak"):
        response = client.delete("/users/1")
    
    assert response.status_code == 204


def test_delete_user_not_found(mock_dao, mock_payload_admin):
    """Usuario a eliminar no existe"""
    mock_dao.get_user.return_value = None
    
    client = TestClient(make_users_app(mock_dao, mock_payload_admin))
    response = client.delete("/users/999")
    
    assert response.status_code == 404


def test_delete_user_forbidden_different_user(mock_dao, mock_payload_user):
    """Eliminar usuario diferente sin ser admin"""
    user = {
        "user_id": 2,
        "user_name": "other_user",
        "role_id": 2,
        "keycloak_id": "other-keycloak-user"
    }
    mock_dao.get_user.return_value = user
    
    client = TestClient(make_users_app(mock_dao, mock_payload_user))
    response = client.delete("/users/2")
    
    assert response.status_code == 403
