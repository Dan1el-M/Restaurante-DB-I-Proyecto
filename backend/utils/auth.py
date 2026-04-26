def has_admin_role(payload: dict) -> bool:
    roles = payload.get("realm_access", {}).get("roles", [])
    return "admin" in roles