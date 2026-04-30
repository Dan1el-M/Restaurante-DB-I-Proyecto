"""
Router de usuarios autenticados
"""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.app.autentificador.keycloak_register_admin import (
    delete_user_from_keycloak,
    update_user_in_keycloak,
)
from backend.dao import BaseDAO, field_value
from backend.database import get_dao
from backend.utils.auth import has_admin_role
from backend.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/me", response_model=UserResponse)
def get_me(
    payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """
    Devuelve el usuario autenticado según el `sub` del token de Keycloak.
    """
    keycloak_sub = payload.get("sub")
    if not keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin claim 'sub'",
        )

    user = dao.get_user_by_keycloak_id(keycloak_sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en BD",
        )

    return user
# Aquí irán los endpoints de usuarios (admin)

@router.put("/{user_id}", response_model=UserResponse)
def update_me(
    user_id: int,
    data: UserUpdate,
    payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """
    Actualiza el perfil del usuario autenticado.
    """
    keycloak_sub = payload.get("sub")
    if not keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin claim 'sub'",
        )

    user = dao.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en BD",
        )

    # Solo admin o dueño del recurso puede actualizar
    if field_value(user, "keycloak_id") != keycloak_sub and not has_admin_role(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario",
        )

    # No permitir escalar privilegios desde este endpoint
    if data.role_id is not None and data.role_id != field_value(user, "role_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes cambiar tu rol desde este endpoint",
        )

    if data.user_name is not None:
        existing_user = dao.get_user_by_username(data.user_name)
        if existing_user and field_value(existing_user, "user_id") != field_value(user, "user_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso",
            )

        keycloak_id = field_value(user, "keycloak_id")
        if keycloak_id:
            try:
                update_user_in_keycloak(keycloak_id, data.user_name)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"No se pudo actualizar el usuario en Keycloak: {str(exc)}",
                )

        user = dao.update_user(user_id, {"user_name": data.user_name})

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    user_id: int,
    payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """
    Elimina la cuenta del usuario autenticado en Keycloak y en la BD local.
    """
    keycloak_sub = payload.get("sub")
    if not keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin claim 'sub'",
        )

    user = dao.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en BD",
        )

    # Solo admin o dueño del recurso puede eliminar
    if field_value(user, "keycloak_id") != keycloak_sub and not has_admin_role(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este usuario",
        )

    keycloak_id = field_value(user, "keycloak_id")
    if keycloak_id:
        try:
            delete_user_from_keycloak(keycloak_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo eliminar el usuario en Keycloak: {str(exc)}",
            )

    dao.delete_user(user_id)
    return None
