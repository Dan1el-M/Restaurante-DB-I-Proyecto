"""Tests unitarios para router de autenticación"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.schemas.auth import RegisterRequest, LoginRequest


def test_register_request_valid():
    """Registro válido con schema"""
    data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "securepass123"
    }
    req = RegisterRequest(**data)
    assert req.username == "john_doe"
    assert req.email == "john@example.com"


def test_register_request_missing_fields():
    """Registro con campos faltantes"""
    data = {
        "username": "john_doe",
        "email": "john@example.com"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_invalid_email():
    """Email inválido"""
    data = {
        "username": "john_doe",
        "email": "invalid-email",
        "password": "securepass123"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_short_password():
    """Password muy corto"""
    data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "short"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_login_request_valid():
    """Login válido"""
    data = {
        "username": "john_doe",
        "password": "password123"
    }
    req = LoginRequest(**data)
    assert req.username == "john_doe"
    assert req.password == "password123"


def test_login_request_short_username():
    """Username muy corto"""
    data = {
        "username": "ab",
        "password": "password123"
    }
    with pytest.raises(ValidationError):
        LoginRequest(**data)
