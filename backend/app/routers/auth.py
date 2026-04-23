"""
Router de autenticación: registro y login
"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.users import User
from backend.models.roles import Role
from backend.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest
from backend.app.autentificador.keycloak_register_admin import create_user_in_keycloak
#from backend.app.autentificador.keycloak_register_client import login as keycloak_login
from backend.app.autentificador.keycloak_login import login as keycloak_login

router = APIRouter(prefix="/auth", tags=["Autenticación"])

KEYCLOAK_REQUIRED_ENV = ["KEYCLOAK_URL", "KEYCLOAK_REALM", "KEYCLOAK_ADMIN_PASSWORD"]


def _missing_keycloak_env_vars():
    missing = [var for var in KEYCLOAK_REQUIRED_ENV if not os.getenv(var)]

    # El usuario admin puede venir en cualquiera de estas dos variables
    admin_user = os.getenv("KEYCLOAK_ADMIN_USER") or os.getenv("KEYCLOAK_ADMIN_USERNAME")
    if not admin_user:
        missing.append("KEYCLOAK_ADMIN_USER o KEYCLOAK_ADMIN_USERNAME")

    return missing

# ========== POST /auth/register ==========

@router.post("/register", status_code=201, response_model=RegisterResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username
    email = payload.email
    password = payload.password

    """
    Registra un nuevo usuario en Keycloak y en la BD
    
    Args:
        username: nombre de usuario
        email: email del usuario
        password: contraseña
    
    Retorna: {'message': 'Usuario creado', 'user_id': id}
    """
    
    # ========== VALIDACIONES ==========
    
    if not username or not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username, email y password son requeridos"
        )
    missing_keycloak_vars = _missing_keycloak_env_vars()
    if missing_keycloak_vars:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Servicio de autenticación no configurado. "
                f"Faltan variables: {', '.join(missing_keycloak_vars)}"
            ),
        )
    
    # Validar que el usuario no exista en la BD
    existing_user = db.query(User).filter(User.user_name == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe"
        )
    
    # ========== PASO 1: CREAR EN KEYCLOAK ==========
    
    try:
        keycloak_id = create_user_in_keycloak(
            username=username,
            email=email,
            password=password,
            role="client"  # Los que se registran son clientes
        )
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if "Faltan variables de entorno" in str(e):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        raise HTTPException(
            status_code=status_code,
            detail=f"Error al crear usuario en Keycloak: {str(e)}"
        )
    
    # ========== PASO 2: CREAR EN LA BD ==========
    
    try:
        role = db.query(Role).filter(Role.role_name == "client").first()
        if not role:
            raise HTTPException(
                status_code=500,
                detail="Rol 'client' no existe en la base de datos"
            )
        new_user = User(
            user_name=username,
            keycloak_id=keycloak_id,
            role_id=role.role_id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        # Si falla en la BD, intentar eliminar el usuario de Keycloak
        from backend.app.autentificador.keycloak_register_admin import delete_user_from_keycloak
        try:
            delete_user_from_keycloak(keycloak_id)
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario en BD: {str(e)}"
        )
    
    # ========== RESPUESTA ==========
    
    return {
        "message": "Usuario creado correctamente",
        "user_id": new_user.user_id,
        "username": new_user.user_name
    }


# ========== POST /auth/login ==========

@router.post("/login")
def login(payload: LoginRequest):
    token_response = keycloak_login(payload.username, payload.password)
    return token_response