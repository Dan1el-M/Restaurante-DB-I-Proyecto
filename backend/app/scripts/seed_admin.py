import os
import time
import requests
import psycopg2
from psycopg2 import OperationalError


KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "restaurant-realm")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin")

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "restaurant_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


def wait_for_keycloak(max_retries=30, delay=3):
    url = f"{KEYCLOAK_URL}/realms/master"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("Keycloak listo.")
                return
        except requests.exceptions.RequestException:
            pass

        print(f"Esperando Keycloak... intento {attempt}")
        time.sleep(delay)

    raise Exception("Keycloak no estuvo listo a tiempo")


def wait_for_postgres(max_retries=30, delay=3):
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            conn.close()
            print("PostgreSQL listo.")
            return
        except OperationalError:
            print(f"Esperando PostgreSQL... intento {attempt}")
            time.sleep(delay)

    raise Exception("PostgreSQL no estuvo listo a tiempo")


def get_admin_token():
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

    data = {
        "client_id": "admin-cli",
        "username": KEYCLOAK_ADMIN_USER,
        "password": KEYCLOAK_ADMIN_PASSWORD,
        "grant_type": "password",
    }

    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    return response.json()["access_token"]


def get_or_create_keycloak_user(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    users_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"

    search_response = requests.get(
        users_url,
        headers=headers,
        params={"username": ADMIN_USERNAME},
        timeout=10,
        #que el temporary sea false para que no pida cambiar la contraseña al primer login
    )
    search_response.raise_for_status()

    users = search_response.json()

    if users:
        print("Usuario admin ya existe en Keycloak.")
        return users[0]["id"]

    payload = {
        "username": ADMIN_USERNAME,
        "firstName": "Admin",
        "lastName": "User",
        "email": ADMIN_EMAIL,
        "enabled": True,
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": ADMIN_PASSWORD,
                "temporary": False,
            }
        ],
    }

    create_response = requests.post(
        users_url,
        headers=headers,
        json=payload,
        timeout=10,
    )
    create_response.raise_for_status()

    search_response = requests.get(
        users_url,
        headers=headers,
        params={"username": ADMIN_USERNAME},
        timeout=10,
    )
    search_response.raise_for_status()

    print("Usuario admin creado en Keycloak.")
    return search_response.json()[0]["id"]


def insert_admin_in_postgres(keycloak_id):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_name, role_id, keycloak_id)
                    VALUES (
                        %s,
                        (SELECT role_id FROM roles WHERE role_name = 'admin'),
                        %s
                    )
                    ON CONFLICT (keycloak_id) DO NOTHING;
                """, (ADMIN_USERNAME, keycloak_id))

        print("Usuario admin insertado o ya existente en PostgreSQL.")

    finally:
        conn.close()

def get_or_create_realm_role(token, role_name):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    role_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles/{role_name}"

    response = requests.get(role_url, headers=headers, timeout=10)

    if response.status_code == 200:
        print(f"Rol '{role_name}' ya existe en Keycloak.")
        return response.json()

    if response.status_code != 404:
        response.raise_for_status()

    create_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles"

    payload = {
        "name": role_name,
        "description": f"Rol {role_name} del sistema de restaurantes",
    }

    create_response = requests.post(
        create_url,
        headers=headers,
        json=payload,
        timeout=10,
    )
    create_response.raise_for_status()

    response = requests.get(role_url, headers=headers, timeout=10)
    response.raise_for_status()

    print(f"Rol '{role_name}' creado en Keycloak.")
    return response.json()

def assign_realm_role_to_user(token, user_id, role):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    assign_url = (
        f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}"
        f"/users/{user_id}/role-mappings/realm"
    )

    payload = [
        {
            "id": role["id"],
            "name": role["name"],
        }
    ]

    response = requests.post(
        assign_url,
        headers=headers,
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

    print(f"Rol '{role['name']}' asignado al usuario admin en Keycloak.")

def main():
    wait_for_keycloak()
    wait_for_postgres()

    token = get_admin_token()

    admin_role = get_or_create_realm_role(token, "admin")
    get_or_create_realm_role(token, "client")

    keycloak_id = get_or_create_keycloak_user(token)

    assign_realm_role_to_user(token, keycloak_id, admin_role)

    insert_admin_in_postgres(keycloak_id)

    print("Seed admin completado correctamente.")


if __name__ == "__main__":
    main()