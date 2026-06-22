import os

# Clave requerida por Superset para firmar sesiones y proteger formularios.
# En Docker Compose se puede sobrescribir con SUPERSET_SECRET_KEY.
SECRET_KEY = os.getenv(
    "SUPERSET_SECRET_KEY",
    "restaurant_superset_local_secret_change_me",
)

# Base de metadatos interna de Superset. Guarda usuarios, conexiones,
# datasets, charts y dashboards en el volumen superset_home.
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_METADATA_DB_URI",
    "sqlite:////app/superset_home/superset.db",
)

# Mantiene la entrega enfocada en los dashboards del proyecto, no en ejemplos demo.
SUPERSET_LOAD_EXAMPLES = False

# Permite usar consultas SQL como base para datasets virtuales y charts.
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}
