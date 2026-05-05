"""Tests unitarios para schemas"""
import pytest
from pydantic import ValidationError
from backend.schemas.auth import RegisterRequest, LoginRequest
from backend.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse


class TestRegisterRequest:
    """Pruebas para RegisterRequest schema"""
    
    def test_valid_register_request(self):
        """Registro válido"""
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepass123"
        }
        req = RegisterRequest(**data)
        assert req.username == "john_doe"
        assert req.email == "john@example.com"
        assert req.password == "securepass123"
    
    def test_register_request_short_username(self):
        """Username muy corto"""
        data = {
            "username": "ab",
            "email": "john@example.com",
            "password": "securepass123"
        }
        with pytest.raises(ValidationError):
            RegisterRequest(**data)
    
    def test_register_request_short_password(self):
        """Password muy corto"""
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "short"
        }
        with pytest.raises(ValidationError):
            RegisterRequest(**data)
    
    def test_register_request_invalid_email(self):
        """Email inválido"""
        data = {
            "username": "john_doe",
            "email": "invalid-email",
            "password": "securepass123"
        }
        with pytest.raises(ValidationError):
            RegisterRequest(**data)
    
    def test_register_request_missing_field(self):
        """Campo requerido ausente"""
        data = {
            "username": "john_doe",
            "email": "john@example.com"
        }
        with pytest.raises(ValidationError):
            RegisterRequest(**data)


class TestLoginRequest:
    """Pruebas para LoginRequest schema"""
    
    def test_valid_login_request(self):
        """Login válido"""
        data = {
            "username": "john_doe",
            "password": "securepass123"
        }
        req = LoginRequest(**data)
        assert req.username == "john_doe"
        assert req.password == "securepass123"
    
    def test_login_request_short_username(self):
        """Username muy corto"""
        data = {
            "username": "ab",
            "password": "password"
        }
        with pytest.raises(ValidationError):
            LoginRequest(**data)
    
    def test_login_request_empty_password(self):
        """Password vacío no es válido (min_length=1)"""
        data = {
            "username": "john_doe",
            "password": ""
        }
        with pytest.raises(ValidationError):
            LoginRequest(**data)


class TestUserCreate:
    """Pruebas para UserCreate schema"""
    
    def test_valid_user_create(self):
        """Creación válida de usuario"""
        data = {
            "user_name": "john_doe",
            "role_id": 1
        }
        user = UserCreate(**data)
        assert user.user_name == "john_doe"
        assert user.role_id == 1
    
    def test_user_create_invalid_role_id(self):
        """role_id debe ser > 0"""
        data = {
            "user_name": "john_doe",
            "role_id": 0
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_negative_role_id(self):
        """role_id negativo no válido"""
        data = {
            "user_name": "john_doe",
            "role_id": -1
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)


class TestUserUpdate:
    """Pruebas para UserUpdate schema"""
    
    def test_user_update_partial(self):
        """Actualización parcial"""
        data = {
            "user_name": "jane_doe"
        }
        update = UserUpdate(**data)
        assert update.user_name == "jane_doe"
        assert update.role_id is None
    
    def test_user_update_all_fields(self):
        """Actualización completa"""
        data = {
            "user_name": "jane_doe",
            "role_id": 2
        }
        update = UserUpdate(**data)
        assert update.user_name == "jane_doe"
        assert update.role_id == 2
    
    def test_user_update_empty(self):
        """Sin campos a actualizar"""
        data = {}
        update = UserUpdate(**data)
        assert update.user_name is None
        assert update.role_id is None


class TestUserResponse:
    """Pruebas para UserResponse schema"""
    
    def test_valid_user_response(self):
        """Response válida"""
        data = {
            "user_id": 1,
            "user_name": "john_doe",
            "role_id": 1
        }
        response = UserResponse(**data)
        assert response.user_id == 1
        assert response.user_name == "john_doe"


class TestRestaurantCreate:
    """Pruebas para RestaurantCreate schema"""
    
    def test_valid_restaurant_create(self):
        """Creación válida de restaurante"""
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


class TestRestaurantUpdate:
    """Pruebas para RestaurantUpdate schema"""
    
    def test_restaurant_update_partial(self):
        """Actualización parcial"""
        data = {
            "restaurant_name": "New Name"
        }
        update = RestaurantUpdate(**data)
        assert update.restaurant_name == "New Name"
        assert update.admin_id is None
    
    def test_restaurant_update_empty(self):
        """Sin campos a actualizar"""
        data = {}
        update = RestaurantUpdate(**data)
        assert update.restaurant_name is None
        assert update.admin_id is None


class TestRestaurantResponse:
    """Pruebas para RestaurantResponse schema"""
    
    def test_valid_restaurant_response(self):
        """Response válida"""
        data = {
            "restaurant_id": 1,
            "restaurant_name": "La Pizzeria",
            "admin_id": 1,
            "restaurant_status": 1
        }
        response = RestaurantResponse(**data)
        assert response.restaurant_id == 1
        assert response.restaurant_name == "La Pizzeria"
