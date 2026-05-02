from backend.utils.auth import has_admin_role


def test_has_admin_role_returns_true_when_admin_exists():
    """Valida que has_admin_role retorna True cuando token contiene rol 'admin'."""
    payload = {"realm_access": {"roles": ["client", "admin"]}}
    assert has_admin_role(payload) is True


def test_has_admin_role_returns_false_when_admin_missing():
    """Valida que has_admin_role retorna False cuando falta rol 'admin'."""
    payload = {"realm_access": {"roles": ["client"]}}
    assert has_admin_role(payload) is False


def test_has_admin_role_handles_empty_payload():
    """Valida que has_admin_role retorna False con payload vacío (sin crash)."""
    assert has_admin_role({}) is False
