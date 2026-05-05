"""Tests unitarios para schemas de usuarios"""
import pytest
from pydantic import ValidationError
from backend.schemas.user import UserCreate, UserUpdate, UserResponse


class TestUserSchemas:
    """Pruebas para schemas de usuarios"""
    
    def test_user_create_valid(self):
        """Crear usuario válido"""
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
    
    def test_user_update_partial(self):
        """Actualización parcial de usuario"""
        data = {
            "user_name": "jane_doe"
        }
        update = UserUpdate(**data)
        assert update.user_name == "jane_doe"
        assert update.role_id is None
    
    def test_user_update_all_fields(self):
        """Actualización completa de usuario"""
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
    
    def test_user_response_valid(self):
        """Response válida de usuario"""
        data = {
            "user_id": 1,
            "user_name": "john_doe",
            "role_id": 1
        }
        response = UserResponse(**data)
        assert response.user_id == 1
        assert response.user_name == "john_doe"
    
    def test_user_create_empty_name(self):
        """Nombre vacío no es válido"""
        data = {
            "user_name": "",
            "role_id": 1
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_long_name(self):
        """Nombre muy largo"""
        data = {
            "user_name": "a" * 65,  # máximo 64
            "role_id": 1
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)
