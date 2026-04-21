"""
Script para crear roles en el cliente Keycloak
Ejecutar: python backend/create_keycloak_roles.py
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

print("=" * 80)
print("CREAR ROLES EN KEYCLOAK")
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
        print(f"  {response.text}")
        exit(1)
    
    admin_token = response.json().get("access_token")
    print(f"✓ Token de admin obtenido")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Headers con el token de admin
headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

# Obtener el ID del cliente
print(f"\n[PASO 2] Buscando cliente '{KEYCLOAK_CLIENT_ID}'...")
clients_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients"

try:
    response = requests.get(clients_url, headers=headers, timeout=5)
    if not response.ok:
        print(f"✗ Error: {response.status_code}")
        exit(1)
    
    clients = response.json()
    client_id = None
    
    for client in clients:
        if client.get("clientId") == KEYCLOAK_CLIENT_ID:
            client_id = client.get("id")
            break
    
    if not client_id:
        print(f"✗ Cliente '{KEYCLOAK_CLIENT_ID}' no encontrado")
        print(f"  Clientes disponibles: {[c.get('clientId') for c in clients]}")
        exit(1)
    
    print(f"✓ Cliente encontrado (ID: {client_id})")
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Roles a crear
roles_to_create = [
    {
        "name": "admin",
        "description": "Administrador del restaurante"
    },
    {
        "name": "client",
        "description": "Cliente del restaurante"
    }
]

print(f"\n[PASO 3] Creando roles...")
roles_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_id}/roles"

for role_data in roles_to_create:
    role_name = role_data["name"]
    print(f"\n  Creando rol: {role_name}")
    
    try:
        response = requests.post(roles_url, json=role_data, headers=headers, timeout=5)
        
        if response.status_code == 201:
            print(f"    ✓ Rol '{role_name}' creado")
        elif response.status_code == 409:
            print(f"    ⚠ Rol '{role_name}' ya existe")
        else:
            print(f"    ✗ Error: {response.status_code}")
            print(f"      {response.text}")
            
    except Exception as e:
        print(f"    ✗ Error: {e}")

print("\n" + "=" * 80)
print("✓ Roles creados correctamente")
print("=" * 80)
