"""
Router de usuarios (admin)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Usuarios"])

# Aquí irán los endpoints de usuarios (admin)
