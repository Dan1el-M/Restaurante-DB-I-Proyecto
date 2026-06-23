from __future__ import annotations

import json
import os

import requests

from common import env_bool


def main() -> None:
    """
    Llama el endpoint de reindexado del servicio Search.

    Por defecto usa el nombre de servicio Docker `search`, no localhost. Si el
    servicio requiere autenticacion y no hay token disponible, se deja un log
    claro. ALLOW_REINDEX_UNAVAILABLE=true permite que el DAG siga para demos
    donde el stack transaccional/API no esta levantado completo.
    """
    url = os.getenv("SEARCH_REINDEX_URL", "http://search/reindex")
    token = os.getenv("SEARCH_AUTH_TOKEN", "")
    allow_unavailable = env_bool("ALLOW_REINDEX_UNAVAILABLE", True)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print("==> reindex_elasticsearch_if_needed")
    print(f"POST {url}")
    try:
        response = requests.post(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code >= 400:
            raise RuntimeError(f"Search reindex endpoint returned HTTP {response.status_code}")
    except Exception as exc:
        diagnostic = {
            "url": url,
            "allow_reindex_unavailable": allow_unavailable,
            "error": str(exc),
            "hint": "Start search/nginx/api services or provide SEARCH_AUTH_TOKEN if authentication is required.",
        }
        print(json.dumps(diagnostic, indent=2))
        if not allow_unavailable:
            raise


if __name__ == "__main__":
    main()
