from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keycloak_validation import validate_token

security = HTTPBearer()


def require_role(required_role: str):
	def _role_checker(
		credentials: HTTPAuthorizationCredentials = Depends(security),
	):
		token = credentials.credentials
		payload = validate_token(token)

		# Roles in Keycloak are included in realm_access.roles.
		roles = payload.get("realm_access", {}).get("roles", [])
		if required_role not in roles:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="no tienes permisos",
			)

		return payload

	return _role_checker
