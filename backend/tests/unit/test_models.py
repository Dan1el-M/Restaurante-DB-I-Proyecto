"""Tests unitarios para modelos SQLAlchemy"""
import pytest
from backend.models.users import User
from backend.models.restaurants import Restaurant
from backend.models.roles import Role


class TestUserModel:
    """Pruebas para el modelo User"""
    
    def test_user_repr(self):
        """Representación string del usuario"""
        user = User(user_id=1, user_name="john_doe", role_id=1)
        repr_str = repr(user)
        assert "User" in repr_str
        assert "user_id=1" in repr_str
        assert "john_doe" in repr_str
        assert "role_id=1" in repr_str
    
    def test_user_creation(self):
        """Creación de usuario"""
        user = User(user_id=1, user_name="john_doe", role_id=2, keycloak_id="uuid-123")
        assert user.user_id == 1
        assert user.user_name == "john_doe"
        assert user.role_id == 2
        assert user.keycloak_id == "uuid-123"
    
    def test_user_attributes(self):
        """Atributos del usuario"""
        user = User()
        # Verificar que los atributos existen
        assert hasattr(user, "user_id")
        assert hasattr(user, "user_name")
        assert hasattr(user, "keycloak_id")
        assert hasattr(user, "role_id")


class TestRestaurantModel:
    """Pruebas para el modelo Restaurant"""
    
    def test_restaurant_repr(self):
        """Representación string del restaurante"""
        restaurant = Restaurant(
            restaurant_id=1,
            restaurant_name="La Pizzeria",
            admin_id=1,
            restaurant_status=1
        )
        repr_str = repr(restaurant)
        assert "Restaurant" in repr_str
        assert "restaurant_id=1" in repr_str
        assert "La Pizzeria" in repr_str
        assert "restaurant_status=1" in repr_str
    
    def test_restaurant_creation(self):
        """Creación de restaurante"""
        restaurant = Restaurant(
            restaurant_id=1,
            restaurant_name="La Pizzeria",
            admin_id=5,
            restaurant_status=1
        )
        assert restaurant.restaurant_id == 1
        assert restaurant.restaurant_name == "La Pizzeria"
        assert restaurant.admin_id == 5
        assert restaurant.restaurant_status == 1
    
    def test_restaurant_attributes(self):
        """Atributos del restaurante"""
        restaurant = Restaurant()
        assert hasattr(restaurant, "restaurant_id")
        assert hasattr(restaurant, "restaurant_name")
        assert hasattr(restaurant, "admin_id")
        assert hasattr(restaurant, "restaurant_status")
    
    def test_restaurant_default_status(self):
        """Estado por defecto del restaurante"""
        restaurant = Restaurant()
        # El estado por defecto es 1 en la definición de columna
        # pero al crear sin valores, será None hasta persistirse en BD
        assert restaurant.restaurant_status is None


class TestRoleModel:
    """Pruebas para el modelo Role"""
    
    def test_role_creation(self):
        """Creación de rol"""
        role = Role(role_id=1, role_name="admin")
        assert role.role_id == 1
        assert role.role_name == "admin"
    
    def test_role_attributes(self):
        """Atributos del rol"""
        role = Role()
        assert hasattr(role, "role_id")
        assert hasattr(role, "role_name")
