import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keycloak_validation import validate_token

security = HTTPBearer() #obtiene el token delheader del request

'''
conenta la autentificacion de fastaspi con la validacion de keycloak

1-FastAPI recibe una request
2-aquí se extrae el token del header
3-se valida
4-se revisan roles
5-si todo bien, se deja pasar
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


def require_role(required_role: str):
    def _role_checker(
        payload=Depends(get_current_user),
    ):
        # Los roles del cliente se encuentran en resource_access.<client_id>.roles
        client_id = os.getenv("KEYCLOAK_CLIENT_ID", "restaurant-client")
        roles = payload.get("resource_access", {}).get(client_id, {}).get("roles", [])

        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no tienes permisos",
            )

        return payload

    return _role_checker

