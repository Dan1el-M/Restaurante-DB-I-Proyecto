"""
Router de usuarios autenticados
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.database import get_db
from backend.models.users import User
from backend.schemas.user import UserResponse


router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserResponse)
def get_me(
    payload=Depends(get_current_user),
    db: Session = Depends(get_db),
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

    user = db.query(User).filter(User.keycloak_id == keycloak_sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en BD",
        )

    return user
# Aquí irán los endpoints de usuarios (admin)
