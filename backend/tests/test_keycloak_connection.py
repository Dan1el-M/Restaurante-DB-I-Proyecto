"""
Script para probar la integración con Keycloak paso a paso.
Ejecutar: python backend/test_keycloak_connection.py
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv
from jose import jwt

# Agregar el directorio backend al path para poder importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

print("=" * 80)
print("PRUEBA DE CONEXIÓN CON KEYCLOAK")
print("=" * 80)

# PASO 1: Verificar que Keycloak está accesible
print("\n[PASO 1] ¿Keycloak está levantado?")
print(f"  URL: {KEYCLOAK_URL}")
try:
    response = requests.get(f"{KEYCLOAK_URL}/health", timeout=5)
    print(f"  ✓ Keycloak responde: {response.status_code}")
except Exception as e:
    print(f"  ✗ ERROR: No se puede conectar a Keycloak")
    print(f"    Detalle: {e}")
    print("  → Verifica que Docker esté ejecutando: docker-compose up -d")
    exit(1)

# PASO 2: Obtener las claves públicas (JWKS)
print("\n[PASO 2] ¿Se pueden obtener las claves públicas?")
jwks_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
print(f"  URL: {jwks_url}")
try:
    response = requests.get(jwks_url, timeout=5)
    if response.ok:
        jwks = response.json()
        print(f"  ✓ Se obtuvieron {len(jwks.get('keys', []))} claves públicas")
        # Mostrar el KID de la primera clave
        if jwks.get('keys'):
            print(f"    KID: {jwks['keys'][0].get('kid')}")
    else:
        print(f"  ✗ ERROR: Status {response.status_code}")
        print(f"    Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    exit(1)

# PASO 3: Obtener un token (necesita usuario en Keycloak)
print("\n[PASO 3] ¿Se puede obtener un token?")
token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
print(f"  URL: {token_url}")

# Usar usuario de prueba en lugar del admin de Keycloak
test_username = "admin_user"
test_password = "admin123"
print(f"  Intentando login con: {test_username}")

payload = {
    "grant_type": "password",
    "client_id": KEYCLOAK_CLIENT_ID,
    "username": test_username,
    "password": test_password
}

try:
    response = requests.post(token_url, data=payload, timeout=5)
    if response.ok:
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            print(f"  ✓ Token obtenido exitosamente")
            print(f"    Tipo: {token_data.get('token_type')}")
            print(f"    Expira en: {token_data.get('expires_in')} segundos")
            
            # PASO 4: Decodificar el token para ver su contenido
            print("\n[PASO 4] Contenido del token:")
            try:
                # Decodificar sin validar primero para ver qué hay
                unverified_payload = jwt.get_unverified_claims(access_token)
                print(f"  ✓ Token decodificado:")
                print(f"    Usuario: {unverified_payload.get('preferred_username')}")
                print(f"    Roles: {unverified_payload.get('realm_access', {}).get('roles', [])}")
                print(f"    Audience: {unverified_payload.get('aud')}")
                print(f"    Issuer: {unverified_payload.get('iss')}")
                print(f"    Exp: {unverified_payload.get('exp')}")
                
                # PASO 5: Validar el token con nuestro código
                print("\n[PASO 5] ¿Se puede validar el token con python-jose?")
                try:
                    from app.autentificador.keycloak_validation import validate_token
                    
                    validated = validate_token(access_token)
                    print(f"  ✓ Token validado correctamente")
                    print(f"    Payload: {json.dumps(validated, indent=2)}")
                    
                except Exception as e:
                    print(f"  ✗ ERROR en validación: {e}")
                    print(f"    Tipo: {type(e).__name__}")
                    
            except Exception as e:
                print(f"  ✗ ERROR al decodificar token: {e}")
        else:
            print(f"  ✗ No se recibió access_token")
            print(f"    Response: {token_data}")
    else:
        print(f"  ✗ ERROR: Status {response.status_code}")
        print(f"    Response: {response.text}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")

print("\n" + "=" * 80)
print("Resumen: Revisa los pasos anteriores para identificar dónde falla")
print("=" * 80)
