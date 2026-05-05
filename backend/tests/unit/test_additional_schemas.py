"""Tests unitarios para modelos y schemas de restaurantes"""
import pytest
from pydantic import ValidationError
from backend.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from backend.schemas.menu import MenuCreate, MenuResponse
from backend.schemas.table import TableCreate, TableResponse


class TestRestaurantSchemas:
    """Pruebas para schemas de restaurantes"""
    
    def test_restaurant_create_valid(self):
        """Crear restaurante válido"""
        data = {
            "restaurant_name": "La Pizzeria",
            "admin_id": 1,
            "restaurant_status": 1
        }
        restaurant = RestaurantCreate(**data)
        assert restaurant.restaurant_name == "La Pizzeria"
        assert restaurant.admin_id == 1
        assert restaurant.restaurant_status == 1
    
    def test_restaurant_create_invalid_admin_id(self):
        """admin_id debe ser > 0"""
        data = {
            "restaurant_name": "La Pizzeria",
            "admin_id": 0,
            "restaurant_status": 1
        }
        with pytest.raises(ValidationError):
            RestaurantCreate(**data)
    
    def test_restaurant_create_negative_status(self):
        """status debe ser >= 0"""
        data = {
            "restaurant_name": "La Pizzeria",
            "admin_id": 1,
            "restaurant_status": -1
        }
        with pytest.raises(ValidationError):
            RestaurantCreate(**data)
    
    def test_restaurant_update_partial(self):
        """Actualización parcial de restaurante"""
        data = {"restaurant_name": "New Name"}
        update = RestaurantUpdate(**data)
        assert update.restaurant_name == "New Name"
        assert update.admin_id is None
        assert update.restaurant_status is None
    
    def test_restaurant_update_all_fields(self):
        """Actualización completa de restaurante"""
        data = {
            "restaurant_name": "New Name",
            "admin_id": 2,
            "restaurant_status": 0
        }
        update = RestaurantUpdate(**data)
        assert update.restaurant_name == "New Name"
        assert update.admin_id == 2
        assert update.restaurant_status == 0
    
    def test_restaurant_response_valid(self):
        """Response válida de restaurante"""
        data = {
            "restaurant_id": 1,
            "restaurant_name": "La Pizzeria",
            "admin_id": 1,
            "restaurant_status": 1
        }
        response = RestaurantResponse(**data)
        assert response.restaurant_id == 1
        assert response.restaurant_name == "La Pizzeria"


class TestMenuSchemas:
    """Pruebas para schemas de menús"""
    
    def test_menu_create_valid(self):
        """Crear menú válido"""
        data = {
            "dish_name": "Pizza",
            "category": "main",
            "description": "Delicious pizza",
            "price": 12.50,
            "restaurant_id": 1
        }
        menu = MenuCreate(**data)
        assert menu.dish_name == "Pizza"
        assert menu.restaurant_id == 1
    
    def test_menu_create_invalid_price(self):
        """price debe ser > 0"""
        data = {
            "dish_name": "Pizza",
            "category": "main",
            "price": 0,
            "restaurant_id": 1
        }
        with pytest.raises(ValidationError):
            MenuCreate(**data)
    
    def test_menu_response_valid(self):
        """Response válida de menú"""
        data = {
            "menu_id": 1,
            "dish_name": "Pizza",
            "category": "main",
            "description": "Delicious pizza",
            "price": 12.50,
            "restaurant_id": 1
        }
        response = MenuResponse(**data)
        assert response.menu_id == 1
        assert response.dish_name == "Pizza"


class TestTableSchemas:
    """Pruebas para schemas de mesas"""
    
    def test_table_create_valid(self):
        """Crear mesa válida"""
        data = {
            "table_number": 1,
            "table_status": 1,
            "restaurant_id": 1
        }
        table = TableCreate(**data)
        assert table.table_number == 1
        assert table.table_status == 1
    
    def test_table_create_invalid_capacity(self):
        """capacity debe ser > 0"""
        data = {
            "table_number": 1,
            "table_status": -1,
            "restaurant_id": 1
        }
        with pytest.raises(ValidationError):
            TableCreate(**data)
    
    def test_table_response_valid(self):
        """Response válida de mesa"""
        data = {
            "table_id": 1,
            "table_number": 1,
            "table_status": 1,
            "restaurant_id": 1
        }
        response = TableResponse(**data)
        assert response.table_id == 1
        assert response.table_number == 1
