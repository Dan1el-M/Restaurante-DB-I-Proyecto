from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from common import check_tcp, env_bool, project_state_dir


def main() -> None:
    """
    Valida disponibilidad de fuentes transaccionales.

    El proyecto puede correr el pipeline OLAP aunque las fuentes completas no
    esten levantadas, porque el DW actual usa seed reproducible. Para no romper
    la demo local, ALLOW_SOURCE_UNAVAILABLE=true permite continuar dejando logs
    claros. Si se desea modo estricto: ALLOW_SOURCE_UNAVAILABLE=false.
    """
    checks = {
        "postgres": check_tcp(os.getenv("POSTGRES_HOST", "postgres"), int(os.getenv("POSTGRES_PORT", "5432"))),
        "mongo_mongos": check_tcp(os.getenv("MONGO_HOST", "mongos"), int(os.getenv("MONGO_PORT", "27017"))),
    }
    allow_unavailable = env_bool("ALLOW_SOURCE_UNAVAILABLE", True)

    summary = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "allow_source_unavailable": allow_unavailable,
        "status": "success" if any(checks.values()) or allow_unavailable else "failed",
    }
    output_path = project_state_dir() / "source_extract_validation.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("==> extract_from_source")
    print(json.dumps(summary, indent=2))

    if not any(checks.values()) and not allow_unavailable:
        raise RuntimeError("No transactional source is reachable and ALLOW_SOURCE_UNAVAILABLE=false")


if __name__ == "__main__":
    main()
