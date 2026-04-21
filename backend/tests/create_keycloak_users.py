"""
Script para crear usuarios automáticamente en Keycloak
Ejecutar: python backend/create_keycloak_users.py
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
print("CREAR USUARIOS EN KEYCLOAK")
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

# Usuarios a crear
users_to_create = [
    {
        "username": "admin_user",
        "email": "admin@restaurant.com",
        "firstName": "Admin",
        "lastName": "Usuario",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": "admin123",
                "temporary": False
            }
        ],
        "roles": ["admin"]
    },
    {
        "username": "client_user",
        "email": "client@restaurant.com",
        "firstName": "Client",
        "lastName": "Usuario",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": "client123",
                "temporary": False
            }
        ],
        "roles": ["client"]
    }
]

print(f"\n[PASO 2] Creando usuarios en realm '{KEYCLOAK_REALM}'...")

users_api_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"

for user_data in users_to_create:
    username = user_data["username"]
    roles = user_data.pop("roles", [])
    
    print(f"\n  Creando/Buscando usuario: {username}")
    
    try:
        # Crear usuario (o si ya existe, continuar)
        response = requests.post(users_api_url, json=user_data, headers=headers, timeout=5)
        
        user_id = None
        
        if response.status_code == 201:
            # Extraer el user ID del header Location
            user_id = response.headers.get("Location", "").split("/")[-1]
            print(f"    ✓ Usuario creado (ID: {user_id})")
        elif response.status_code == 409:
            # Usuario ya existe, obtener su ID
            print(f"    ⚠ El usuario ya existe, buscando su ID...")
            # Buscar el usuario por nombre
            search_url = f"{users_api_url}?username={username}"
            search_response = requests.get(search_url, headers=headers, timeout=5)
            if search_response.ok:
                users = search_response.json()
                if users:
                    user_id = users[0].get("id")
                    print(f"    ✓ Usuario encontrado (ID: {user_id})")
        else:
            print(f"    ✗ Error: {response.status_code}")
            print(f"      {response.text}")
            continue
        
        # Asignar roles si el usuario fue encontrado
        if user_id and roles:
            print(f"    Asignando roles: {roles}")
            
            # Obtener el ID del cliente restaurant-client
            clients_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients"
            clients_response = requests.get(clients_url, headers=headers, timeout=5)
            
            if clients_response.ok:
                clients = clients_response.json()
                client_id = None
                
                for client in clients:
                    if client.get("clientId") == "restaurant-client":
                        client_id = client.get("id")
                        break
                
                if client_id:
                    # Obtener los roles del cliente
                    roles_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_id}/roles"
                    roles_response = requests.get(roles_url, headers=headers, timeout=5)
                    
                    if roles_response.ok:
                        available_roles = roles_response.json()
                        roles_to_assign = []
                        
                        for role_name in roles:
                            for available_role in available_roles:
                                if available_role.get("name") == role_name:
                                    roles_to_assign.append(available_role)
                                    break
                        
                        if roles_to_assign:
                            # Asignar roles al usuario
                            assign_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/clients/{client_id}"
                            assign_response = requests.post(assign_url, json=roles_to_assign, headers=headers, timeout=5)
                            
                            if assign_response.status_code in [200, 204]:
                                print(f"    ✓ Roles asignados: {roles}")
                            else:
                                print(f"    ✗ Error asignando roles: {assign_response.status_code}")
                        else:
                            print(f"    ⚠ Los roles {roles} no existen en el cliente")
            
    except Exception as e:
        print(f"    ✗ Error: {e}")

print("\n" + "=" * 80)
print("USUARIOS CREADOS:")
print("  • admin_user / admin123 (rol: admin)")
print("  • client_user / client123 (rol: client)")
print("=" * 80)
print("\nPróximo paso: Ejecuta 'python backend/create_keycloak_roles.py' para crear los roles")
print("Luego ejecuta este script nuevamente para asignar los roles a los usuarios.")
