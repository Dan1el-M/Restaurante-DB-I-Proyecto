import os
import time
from urllib.parse import urlparse

import requests
import psycopg2
from pymongo import MongoClient, ReturnDocument
from psycopg2 import OperationalError
from dotenv import load_dotenv


load_dotenv()


KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME")
ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD")

POSTGRES_URL = os.getenv("POSTGRES_URL")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DATABASE_ENGINE = os.getenv("DATABASE_ENGINE").split("#", 1)[0].strip().lower()
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB")

postgres_url = urlparse(POSTGRES_URL.replace("postgresql+psycopg2://", "postgresql://", 1))
DB_HOST = postgres_url.hostname
DB_PORT = postgres_url.port

# Este script lo que hace es colocar el admin tanto como en la base de datos como en el keyclock, para que al iniciar el programa, ya esté definido el admin
def wait_for_keycloak(max_retries=100, delay=4):
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


def wait_for_mongo(max_retries=30, delay=3):
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

    for attempt in range(1, max_retries + 1):
        try:
            client.admin.command("ping")
            print("MongoDB listo.")
            client.close()
            return
        except Exception:
            print(f"Esperando MongoDB... intento {attempt}")
            time.sleep(delay)

    client.close()
    raise Exception("MongoDB no estuvo listo a tiempo")


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

    user_payload = {
        "username": ADMIN_USERNAME,
        "firstName": "Admin",
        "lastName": "User",
        "email": ADMIN_EMAIL,
        "enabled": True,
        "emailVerified": True,
        "firstName": ADMIN_USERNAME,
        "lastName": ADMIN_USERNAME,
        "requiredActions": [],
        "credentials": [
            {
                "type": "password",
                "value": ADMIN_PASSWORD,
                "temporary": False,
            }
        ],
    }

    if users:
        existing_user = users[0]
        user_id = existing_user.get("id")
        if not user_id:
            raise Exception("Usuario existente en Keycloak sin id válido")

        # Reconciliar estado del usuario para evitar errores de login por
        # acciones requeridas pendientes (ej. UPDATE_PROFILE).
        update_url = f"{users_url}/{user_id}"

        update_response = requests.put(
            update_url,
            headers=headers,
            json=user_payload,
            timeout=10,
        )
        update_response.raise_for_status()

        print("Usuario admin ya existe en Keycloak (actualizado).")
        return user_id

    create_response = requests.post(
        users_url,
        headers=headers,
        json=user_payload,
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


def insert_admin_in_mongo(keycloak_id):
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB_NAME]

    try:
        role = db.roles.find_one({"role_name": "admin"})
        if not role:
            role = {"role_id": 1, "role_name": "admin"}
            db.roles.update_one({"role_id": 1}, {"$setOnInsert": role}, upsert=True)

        existing_user = db.users.find_one({"keycloak_id": keycloak_id})
        if not existing_user:
            counter = db.counters.find_one_and_update(
                {"_id": "users"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            db.users.insert_one(
                {
                    "user_id": counter["seq"],
                    "user_name": ADMIN_USERNAME,
                    "keycloak_id": keycloak_id,
                    "role_id": role["role_id"],
                }
            )

        print("Usuario admin insertado o ya existente en MongoDB.")

    finally:
        client.close()

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
    if DATABASE_ENGINE == "mongo":
        wait_for_mongo()
    else:
        wait_for_postgres()

    token = get_admin_token()

    admin_role = get_or_create_realm_role(token, "admin")
    get_or_create_realm_role(token, "client")

    keycloak_id = get_or_create_keycloak_user(token)

    assign_realm_role_to_user(token, keycloak_id, admin_role)

    if DATABASE_ENGINE == "mongo":
        insert_admin_in_mongo(keycloak_id)
    else:
        insert_admin_in_postgres(keycloak_id)

    print("Seed admin completado correctamente.")


if __name__ == "__main__":
    main()
