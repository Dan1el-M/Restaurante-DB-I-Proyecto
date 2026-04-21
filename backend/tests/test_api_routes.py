"""
Script para probar las rutas protegidas de la API
Ejecutar: python backend/test_api_routes.py
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
API_URL = os.getenv("API_URL", "http://localhost:8000")

print("=" * 80)
print("PRUEBA DE RUTAS PROTEGIDAS")
print("=" * 80)

# Usuarios de prueba
test_users = [
    {"username": "admin_user", "password": "admin123", "role": "admin"},
    {"username": "client_user", "password": "client123", "role": "client"}
]

# Para cada usuario, obtener token y probar rutas
for user_info in test_users:
    username = user_info["username"]
    password = user_info["password"]
    role = user_info["role"]
    
    print(f"\n{'=' * 80}")
    print(f"Usuario: {username} (rol: {role})")
    print(f"{'=' * 80}")
    
    # Obtener token
    print(f"\n[1] Obteniendo token...")
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    
    payload = {
        "grant_type": "password",
        "client_id": KEYCLOAK_CLIENT_ID,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(token_url, data=payload, timeout=5)
        if not response.ok:
            print(f"✗ Error obteniendo token: {response.status_code}")
            print(f"  {response.text}")
            continue
        
        access_token = response.json().get("access_token")
        print(f"✓ Token obtenido")
    except Exception as e:
        print(f"✗ Error: {e}")
        continue
    
    # Headers con el token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Rutas a probar
    routes = [
        ("/", "GET", "Ruta pública"),
        ("/test-validate", "GET", "Validar token (protegida)"),
        ("/admin", "GET", "Ruta admin (requiere rol admin)"),
        ("/client", "GET", "Ruta client (requiere rol client)"),
    ]
    
    print(f"\n[2] Probando rutas...")
    print("-" * 80)
    
    for route, method, description in routes:
        url = f"{API_URL}{route}"
        print(f"\n{description}")
        print(f"  URL: {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            
            print(f"  Status: {response.status_code}")
            
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=4)}")
            except:
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("✓ Pruebas completadas")
print("=" * 80)
