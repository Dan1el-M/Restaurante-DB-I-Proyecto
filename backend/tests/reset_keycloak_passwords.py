"""
Script para restablecer contraseñas de usuarios en Keycloak
Ejecutar: python backend/reset_keycloak_passwords.py
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

print("=" * 80)
print("RESTABLECER CONTRASEÑAS DE USUARIOS")
print("=" * 80)

# PASO 1: Obtener token de admin
print("\n[PASO 1] Obteniendo token de administrador...")
token_url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

payload = {
    "grant_type": "password",
    "client_id": "admin-cli",
    "username": KEYCLOAK_ADMIN_USER,
    "password": KEYCLOAK_ADMIN_PASSWORD
}

try:
    response = requests.post(token_url, data=payload, timeout=5)
    if not response.ok:
        print(f"✗ Error: {response.status_code}")
        exit(1)
    
    admin_token = response.json().get("access_token")
    print(f"✓ Token de admin obtenido")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

# Usuarios a actualizar
users_to_update = [
    {"username": "admin_user", "password": "admin123"},
    {"username": "client_user", "password": "client123"}
]

print(f"\n[PASO 2] Actualizando contraseñas...")
users_api_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"

for user_data in users_to_update:
    username = user_data["username"]
    password = user_data["password"]
    
    print(f"\n  Buscando usuario: {username}")
    
    try:
        # Buscar el usuario
        search_url = f"{users_api_url}?username={username}"
        search_response = requests.get(search_url, headers=headers, timeout=5)
        
        if search_response.ok:
            users = search_response.json()
            if users:
                user_id = users[0].get("id")
                print(f"    ✓ Usuario encontrado (ID: {user_id})")
                
                # Actualizar contraseña
                password_url = f"{users_api_url}/{user_id}/reset-password"
                password_payload = {
                    "type": "password",
                    "value": password,
                    "temporary": False
                }
                
                password_response = requests.put(password_url, json=password_payload, headers=headers, timeout=5)
                
                if password_response.status_code in [200, 204]:
                    print(f"    ✓ Contraseña actualizada: {password}")
                else:
                    print(f"    ✗ Error: {password_response.status_code}")
                    print(f"      {password_response.text}")
            else:
                print(f"    ✗ Usuario no encontrado")
        else:
            print(f"    ✗ Error en búsqueda: {search_response.status_code}")
            
    except Exception as e:
        print(f"    ✗ Error: {e}")

print("\n" + "=" * 80)
print("✓ Contraseñas restablecidas")
print("=" * 80)
