"""
Router de usuarios (admin)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.users import User
from backend.schemas.user import UserResponse
from backend.app.autentificador.keycloak_dependencies import get_current_user


router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/me", response_model=UserResponse)
def get_me(payload=Depends(get_current_user), db: Session = Depends(get_db)):
    keycloak_sub = payload.get("sub")
    if not keycloak_sub:
        raise HTTPException(status_code=401, detail="Token sin claim 'sub'")

    user = db.query(User).filter(User.keycloak_id == keycloak_sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en BD")

    return user
# Aquí irán los endpoints de usuarios (admin)
