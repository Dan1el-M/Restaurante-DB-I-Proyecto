"""
Funciones para que los clientes hagan login en Keycloak
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()


# ========== LOGIN ==========

def login(username: str, password: str):
    """
    Autentica un usuario contra Keycloak y devuelve el token de acceso
    
    Args:
        username: nombre de usuario
        password: contraseña
    
    Retorna: diccionario con access_token, refresh_token, token_type, expires_in, etc.
    Lanza: Exception si las credenciales son inválidas o hay error de conexión
    """
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
    
    if not all([keycloak_url, realm, client_id]):
        raise Exception("Faltan variables de entorno de Keycloak")
    
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
    }
    
    # Si hay client_secret (para clientes confidenciales)
    if client_secret:
        data["client_secret"] = client_secret
    
    # ========== REINTENTAR 5 VECES ==========
    # Esto es importante porque a veces Keycloak tarda en estar listo
    
    for intento in range(5):
        try:
            response = requests.post(token_url, data=data, timeout=10)
            
            # Si obtiene respuesta, salir del loop
            break
        
        except requests.exceptions.RequestException:
            # Si aún hay intentos, esperar y reintentar
            if intento < 4:
                time.sleep(3)
            else:
                raise Exception("No se pudo conectar a Keycloak después de 5 intentos")
    
    # ========== MANEJAR RESPUESTA ==========
    
    if response.status_code != 200:
        raise Exception("Credenciales inválidas o usuario no existe")
    
    return response.json()
