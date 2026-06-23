from pathlib import Path


path = Path("/app/superset/db_engine_specs/hive.py")
text = path.read_text(encoding="utf-8")
needle = "    supports_dynamic_schema = True\n"
replacement = """    supports_dynamic_schema = True

    @classmethod
    def get_catalog_names(cls, database, inspector):
        return set()
"""

if replacement not in text:
    if needle not in text:
        raise RuntimeError("Could not find HiveEngineSpec insertion point")
    path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
