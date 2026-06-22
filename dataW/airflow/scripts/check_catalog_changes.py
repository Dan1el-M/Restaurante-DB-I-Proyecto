from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from common import env_bool, exec_in_container, project_state_dir


HIVE_CONTAINER = "hiveserver2"
WAREHOUSE_JDBC = "jdbc:hive2://localhost:10000/restaurant_warehouse"


def beeline(query: str) -> str:
    return exec_in_container(
        HIVE_CONTAINER,
        ["/opt/hive/bin/beeline", "-u", WAREHOUSE_JDBC, "--silent=true", "--showHeader=false", "-e", query],
    )


def product_catalog_fingerprint() -> str:
    output = beeline(
        """
        SELECT
            product_id,
            product_name,
            category,
            subcategory,
            price,
            cost
        FROM dim_product
        ORDER BY product_id;
        """
    )
    normalized = "\n".join(line.strip() for line in output.splitlines() if line.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def main() -> None:
    """
    Detecta cambios en dim_product mediante hash persistido.

    FORCE_REINDEX_PRODUCTS=true fuerza el branch de reindexado.
    REINDEX_ON_FIRST_RUN=false evita reindexar en la primera corrida cuando solo
    se esta inicializando el estado del pipeline.
    """
    state_file = project_state_dir() / "product_catalog_state.json"
    current_hash = product_catalog_fingerprint()
    previous_hash = None
    if state_file.exists():
        previous_hash = json.loads(state_file.read_text(encoding="utf-8")).get("catalog_hash")

    force_reindex = env_bool("FORCE_REINDEX_PRODUCTS", False)
    reindex_on_first_run = env_bool("REINDEX_ON_FIRST_RUN", False)
    first_run = previous_hash is None
    changed = force_reindex or (current_hash != previous_hash and (not first_run or reindex_on_first_run))

    state = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "catalog_hash": current_hash,
        "previous_hash": previous_hash,
        "force_reindex": force_reindex,
        "reindex_on_first_run": reindex_on_first_run,
        "catalog_changed": changed,
    }
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("==> check_product_catalog_changes")
    print(json.dumps(state, indent=2))
    print(f"CATALOG_CHANGED={'true' if changed else 'false'}")


if __name__ == "__main__":
    main()
