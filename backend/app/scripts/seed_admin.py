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
KEYCLOAK_REALM = os.getenv("SEED_KEYCLOAK_TARGET_REALM") or os.getenv("KEYCLOAK_REALM")
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




def wait_for_realm(max_retries=60, delay=3):
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Realm '{KEYCLOAK_REALM}' listo.")
                return
        except requests.exceptions.RequestException:
            pass

        print(f"Esperando realm {KEYCLOAK_REALM}... intento {attempt}")
        time.sleep(delay)

    raise Exception(f"Realm '{KEYCLOAK_REALM}' no estuvo listo a tiempo")

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

    if not ADMIN_USERNAME:
        raise ValueError("SEED_ADMIN_USERNAME no esta configurado")
    if not ADMIN_PASSWORD:
        raise ValueError("SEED_ADMIN_PASSWORD no esta configurado")

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
        "enabled": True,
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

    # Keycloak devuelve 400 si se manda email=null o email invalido.
    if ADMIN_EMAIL:
        user_payload["email"] = ADMIN_EMAIL
        user_payload["emailVerified"] = True

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
        if update_response.status_code >= 400:
            raise Exception(
                "Error actualizando usuario admin en Keycloak "
                f"({update_response.status_code}): {update_response.text}"
            )

        print("Usuario admin ya existe en Keycloak (actualizado).")
        return user_id

    create_response = requests.post(
        users_url,
        headers=headers,
        json=user_payload,
        timeout=10,
    )
    if create_response.status_code >= 400:
        raise Exception(
            "Error creando usuario admin en Keycloak "
            f"({create_response.status_code}): {create_response.text}"
        )

    # Keycloak suele responder 201 (Created) o 204 (No Content) en create user.
    if create_response.status_code not in (201, 204):
        raise Exception(
            "Respuesta inesperada creando usuario admin en Keycloak "
            f"({create_response.status_code}): {create_response.text}"
        )

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
    if create_response.status_code >= 400:
        raise Exception(
            f"Error creando rol '{role_name}' en Keycloak "
            f"({create_response.status_code}): {create_response.text}"
        )

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
    if not KEYCLOAK_REALM:
        raise ValueError("KEYCLOAK_REALM/SEED_KEYCLOAK_TARGET_REALM no esta configurado")

    wait_for_keycloak()
    wait_for_realm()
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
