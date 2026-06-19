
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class KeycloakLoginError(Exception):
    """Error controlado al autenticar contra Keycloak."""

    def __init__(self, message: str, keycloak_error: str | None = None):
        super().__init__(message)
        self.keycloak_error = keycloak_error


def login(username: str, password: str) -> dict:

    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")

    if not all([keycloak_url, realm, client_id]):
        raise KeycloakLoginError("Faltan variables de entorno de Keycloak")

    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
    }

    if client_secret:
        data["client_secret"] = client_secret

    response = None
    for intento in range(5):
        try:
            response = requests.post(token_url, data=data, timeout=10)
            break
        except requests.exceptions.RequestException:
            if intento < 4:
                time.sleep(3)
            else:
                raise KeycloakLoginError("No se pudo conectar a Keycloak después de 5 intentos")

    if response is None:
        raise KeycloakLoginError("No se recibió respuesta de Keycloak")

    if response.status_code != 200:
        keycloak_error = None
        try:
            error_payload = response.json()
            keycloak_error = error_payload.get("error_description") or error_payload.get("error")
        except ValueError:
            keycloak_error = response.text or None

        if keycloak_error and "resolve_required_actions" in keycloak_error:
            raise KeycloakLoginError(
                "El usuario tiene acciones requeridas pendientes en Keycloak "
                "(ej. completar perfil, verificar email o actualizar contraseña).",
                keycloak_error=keycloak_error,
            )

        raise KeycloakLoginError(
            "Credenciales inválidas o usuario no existe",
            keycloak_error=keycloak_error,
        )

    return response.json()