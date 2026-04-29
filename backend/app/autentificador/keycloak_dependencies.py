import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keycloak_validation import validate_token

security = HTTPBearer()  # obtiene el token del header del request

'''
Conecta la autenticación de FastAPI con la validación de Keycloak.

1. FastAPI recibe una request
2. aquí se extrae el token del header
3. se valida
4. se revisan roles
5. si todo bien, se deja pasar
'''

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = validate_token(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token inválido o expirado",
        )



def _extract_roles(payload: dict) -> set[str]:
    """Obtiene roles de realm y de cliente para soportar ambas configuraciones."""
    client_id = os.getenv("KEYCLOAK_CLIENT_ID", "restaurant-client")

    realm_roles = payload.get("realm_access", {}).get("roles", [])
    client_roles = payload.get("resource_access", {}).get(client_id, {}).get("roles", [])

    return set(realm_roles) | set(client_roles)


def require_role(required_role: str):
    def _role_checker(
        payload=Depends(get_current_user),
    ):
        # Los roles del cliente se encuentran en resource_access.<client_id>.roles
        client_id = os.getenv("KEYCLOAK_CLIENT_ID", "restaurant-client")
        roles = _extract_roles(payload)

        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"no tienes permisos (roles actuales: {sorted(roles)})",
            )

        return payload

    return _role_checker

