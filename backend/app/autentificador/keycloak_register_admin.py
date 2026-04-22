"""
Funciones para crear usuarios en Keycloak usando las credenciales de admin
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ========== OBTENER TOKEN DE ADMIN ==========

def get_admin_token():
    """
    Obtiene el token de admin de Keycloak para poder crear usuarios
    
    Retorna: token de admin (string)
    Lanza: Exception si no puede conectar o las credenciales son inválidas
    """
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    admin_username = os.getenv("KEYCLOAK_ADMIN_USER") or os.getenv("KEYCLOAK_ADMIN_USERNAME")
    admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
    
    if not all([keycloak_url, realm, admin_username, admin_password]):
        raise Exception("Faltan variables de entorno de Keycloak admin")
    
    token_url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
    
    # El admin siempre usa el realm "master"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": admin_username,
        "password": admin_password,
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code != 200:
            raise Exception(f"No se pudo obtener token de admin: {response.text}")
        
        return response.json()["access_token"]
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error conectando a Keycloak: {str(e)}")


# ========== CREAR USUARIO EN KEYCLOAK ==========

def create_user_in_keycloak(username: str, email: str, password: str, role: str = "client"):
    """
    Crea un usuario en Keycloak y lo asigna a un rol
    
    Args:
        username: nombre de usuario
        email: email del usuario
        password: contraseña
        role: rol a asignar ("client" o "admin")
    
    Retorna: keycloak_id (UUID del usuario en Keycloak)
    Lanza: Exception si algo falla
    """
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    
    if not keycloak_url or not realm:
        raise Exception("Faltan KEYCLOAK_URL y KEYCLOAK_REALM")
    
    # Obtener token de admin
    admin_token = get_admin_token()
    
    # ========== PASO 1: CREAR USUARIO ==========
    
    user_data = {
        "username": username,
        "email": email,
        "emailVerified": True,
        "enabled": True,
        "firstName": username,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    
    create_url = f"{keycloak_url}/admin/realms/{realm}/users"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(create_url, json=user_data, headers=headers, timeout=10)
        
        if response.status_code not in [201, 200]:
            raise Exception(f"No se pudo crear usuario en Keycloak: {response.text}")
        
        # Extraer el keycloak_id del header Location
        location = response.headers.get("Location", "")
        if location:
            keycloak_id = location.split("/")[-1]
        else:
            # Si no viene en Location, buscar el usuario por username
            search_url = f"{keycloak_url}/admin/realms/{realm}/users?username={username}"
            search_resp = requests.get(search_url, headers=headers, timeout=10)
            if search_resp.status_code == 200 and search_resp.json():
                keycloak_id = search_resp.json()[0]["id"]
            else:
                raise Exception("No se pudo obtener el ID del usuario creado")
        
        # ========== PASO 2: ASIGNAR ROL ==========
        
        # Obtener el role_id del rol a asignar
        roles_url = f"{keycloak_url}/admin/realms/{realm}/roles"
        roles_resp = requests.get(roles_url, headers=headers, timeout=10)
        
        if roles_resp.status_code != 200:
            raise Exception(f"No se pudieron obtener los roles: {roles_resp.text}")
        
        roles = roles_resp.json()
        role_id = None
        
        for r in roles:
            if r["name"] == role:
                role_id = r["id"]
                break
        
        if not role_id:
            raise Exception(f"Rol '{role}' no encontrado en Keycloak")
        
        # Asignar el rol al usuario
        assign_role_url = f"{keycloak_url}/admin/realms/{realm}/users/{keycloak_id}/role-mappings/realm"
        assign_data = [
            {
                "id": role_id,
                "name": role,
                "composite": False,
            }
        ]
        
        assign_resp = requests.post(assign_role_url, json=assign_data, headers=headers, timeout=10)
        
        if assign_resp.status_code not in [201, 204, 200]:
            raise Exception(f"No se pudo asignar rol al usuario: {assign_resp.text}")
        
        return keycloak_id
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error en la solicitud a Keycloak: {str(e)}")


# ========== ELIMINAR USUARIO DE KEYCLOAK ==========

def delete_user_from_keycloak(keycloak_id: str):
    """
    Elimina un usuario de Keycloak
    
    Args:
        keycloak_id: UUID del usuario en Keycloak
    
    Lanza: Exception si algo falla
    """
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    
    if not keycloak_url or not realm:
        raise Exception("Faltan KEYCLOAK_URL y KEYCLOAK_REALM")
    
    admin_token = get_admin_token()
    
    delete_url = f"{keycloak_url}/admin/realms/{realm}/users/{keycloak_id}"
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }
    
    try:
        response = requests.delete(delete_url, headers=headers, timeout=10)
        
        if response.status_code not in [200, 204]:
            raise Exception(f"No se pudo eliminar usuario de Keycloak: {response.text}")
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error en la solicitud a Keycloak: {str(e)}")
