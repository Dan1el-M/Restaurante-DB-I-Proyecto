import os

import requests
from jose import jwt


def get_jwks():
	keycloak_url = os.getenv("KEYCLOAK_URL")
	realm = os.getenv("KEYCLOAK_REALM")
	jwks_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
	# JWKS lets us verify the token signature without a hardcoded public key.
	return requests.get(jwks_url, timeout=5).json()


def validate_token(token: str):
	keycloak_url = os.getenv("KEYCLOAK_URL")
	realm = os.getenv("KEYCLOAK_REALM")
	client_id = os.getenv("KEYCLOAK_CLIENT_ID")

	issuer = f"{keycloak_url}/realms/{realm}"
	jwks = get_jwks()
	headers = jwt.get_unverified_header(token)
	kid = headers.get("kid")

	key = None
	for jwk in jwks.get("keys", []):
		if jwk.get("kid") == kid:
			key = jwk
			break

	if not key:
		raise Exception("public key not found")

	# This validates signature, expiration, issuer, and audience.
	payload = jwt.decode(
		token,
		key,
		algorithms=["RS256"],
		audience=client_id,
		issuer=issuer,
	)
	return payload
