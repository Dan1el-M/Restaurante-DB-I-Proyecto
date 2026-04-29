"""
Compatibilidad histórica.

Este módulo se manteniene para no romper imports antiguos, pero el login real
vive en `keycloak_login.py`.
"""

from .keycloak_login import login

__all__ = ["login"]