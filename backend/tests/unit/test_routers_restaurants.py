"""Tests unitarios para routers - restaurants"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, status
from backend.app.routers import restaurants
from backend.database import get_dao


def make_restaurant_app(mock_dao, token_payload):
    app = FastAPI()
    app.include_router(restaurants.router)
    app.dependency_overrides[get_dao] = lambda: mock_dao
    app.dependency_overrides[restaurants.get_current_user] = lambda: token_payload
    return app


def test_list_restaurants_success(mock_dao, mock_payload_admin):
    """Listar restaurantes exitosamente"""
    # Setup mock
    mock_restaurants = [
        {"restaurant_id": 1, "restaurant_name": "La Pizzeria", "admin_id": 1, "restaurant_status": 1},
        {"restaurant_id": 2, "restaurant_name": "El Sushi", "admin_id": 2, "restaurant_status": 1}
    ]
    mock_dao.list_restaurants.return_value = mock_restaurants
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    response = client.get("/restaurants/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_dao.list_restaurants.assert_called_once()


def test_get_restaurant_success(mock_dao, mock_payload_admin):
    """Obtener restaurante por ID exitosamente"""
    restaurant = {
        "restaurant_id": 1,
        "restaurant_name": "La Pizzeria",
        "admin_id": 1,
        "restaurant_status": 1
    }
    mock_dao.get_restaurant.return_value = restaurant
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    response = client.get("/restaurants/1")
    
    assert response.status_code == 200
    assert response.json()["restaurant_id"] == 1
    assert response.json()["restaurant_name"] == "La Pizzeria"


def test_get_restaurant_not_found(mock_dao, mock_payload_admin):
    """Restaurante no encontrado"""
    mock_dao.get_restaurant.return_value = None
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    response = client.get("/restaurants/999")
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()


def test_create_restaurant_success(mock_dao, mock_payload_admin):
    """Crear restaurante exitosamente"""
    user = {"user_id": 1, "user_name": "admin_user", "role_id": 1}
    mock_dao.get_user.return_value = user
    
    restaurant = {
        "restaurant_id": 1,
        "restaurant_name": "La Pizzeria",
        "admin_id": 1,
        "restaurant_status": 1
    }
    mock_dao.create_restaurant.return_value = restaurant
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    payload = {
        "restaurant_name": "La Pizzeria",
        "admin_id": 1,
        "restaurant_status": 1
    }
    response = client.post("/restaurants/", json=payload)
    
    assert response.status_code == 201
    assert response.json()["restaurant_id"] == 1


def test_create_restaurant_forbidden_not_admin(mock_dao, mock_payload_user):
    """Crear restaurante sin permisos admin"""
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_user))
    payload = {
        "restaurant_name": "La Pizzeria",
        "admin_id": 1,
        "restaurant_status": 1
    }
    response = client.post("/restaurants/", json=payload)
    
    assert response.status_code == 403


def test_create_restaurant_admin_not_exists(mock_dao, mock_payload_admin):
    """Admin del restaurante no existe"""
    mock_dao.get_user.return_value = None
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    payload = {
        "restaurant_name": "La Pizzeria",
        "admin_id": 999,
        "restaurant_status": 1
    }
    response = client.post("/restaurants/", json=payload)
    
    assert response.status_code == 404


def test_update_restaurant_success(mock_dao, mock_payload_admin):
    """Actualizar restaurante exitosamente"""
    restaurant = {
        "restaurant_id": 1,
        "restaurant_name": "La Pizzeria",
        "admin_id": 1,
        "restaurant_status": 1
    }
    mock_dao.update_restaurant.return_value = restaurant
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    payload = {
        "restaurant_name": "La Pizzeria Actualizada"
    }
    response = client.put("/restaurants/1", json=payload)
    
    assert response.status_code == 200


def test_update_restaurant_forbidden(mock_dao, mock_payload_user):
    """Actualizar restaurante sin permisos"""
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_user))
    payload = {"restaurant_name": "New Name"}
    response = client.put("/restaurants/1", json=payload)
    
    assert response.status_code == 403


def test_delete_restaurant_success(mock_dao, mock_payload_admin):
    """Eliminar restaurante exitosamente"""
    mock_dao.delete_restaurant.return_value = True
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    response = client.delete("/restaurants/1")
    
    assert response.status_code == 204


def test_delete_restaurant_not_found(mock_dao, mock_payload_admin):
    """Eliminar restaurante que no existe"""
    mock_dao.delete_restaurant.return_value = False
    
    client = TestClient(make_restaurant_app(mock_dao, mock_payload_admin))
    response = client.delete("/restaurants/999")
    
    assert response.status_code == 404
