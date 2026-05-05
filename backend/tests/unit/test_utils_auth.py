"""Tests unitarios para backend/utils/auth.py"""
import pytest
from backend.utils.auth import has_admin_role


class TestHasAdminRole:
    """Pruebas para la función has_admin_role"""
    
    def test_has_admin_role_with_admin(self):
        """Usuario con rol admin"""
        payload = {
            "realm_access": {
                "roles": ["admin", "user"]
            }
        }
        assert has_admin_role(payload) is True
    
    def test_has_admin_role_without_admin(self):
        """Usuario sin rol admin"""
        payload = {
            "realm_access": {
                "roles": ["user", "client"]
            }
        }
        assert has_admin_role(payload) is False
    
    def test_has_admin_role_empty_roles(self):
        """Usuario con roles vacío"""
        payload = {
            "realm_access": {
                "roles": []
            }
        }
        assert has_admin_role(payload) is False
    
    def test_has_admin_role_no_realm_access(self):
        """Payload sin realm_access"""
        payload = {
            "sub": "user-123"
        }
        assert has_admin_role(payload) is False
    
    def test_has_admin_role_empty_realm_access(self):
        """realm_access vacío"""
        payload = {
            "realm_access": {}
        }
        assert has_admin_role(payload) is False
    
    def test_has_admin_role_only_admin(self):
        """Usuario solo con rol admin"""
        payload = {
            "realm_access": {
                "roles": ["admin"]
            }
        }
        assert has_admin_role(payload) is True
    
    def test_has_admin_role_empty_payload(self):
        """Payload vacío"""
        payload = {}
        assert has_admin_role(payload) is False
