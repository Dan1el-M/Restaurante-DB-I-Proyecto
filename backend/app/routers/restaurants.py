"""
Router de restaurantes
"""

from fastapi import APIRouter

router = APIRouter(prefix="/restaurants", tags=["Restaurantes"])

# Aquí irán los endpoints de restaurantes
