ARG SUPERSET_VERSION=4.1.2
FROM apache/superset:${SUPERSET_VERSION}

USER root

# Instala las librerias necesarias para que Superset pueda hablar con HiveServer2
# mediante SQLAlchemy/PyHive. Esto permite cumplir la arquitectura directa:
# Superset -> HiveServer2 -> vistas OLAP.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libsasl2-dev \
        libsasl2-modules \
    && rm -rf /var/lib/apt/lists/*

# PyHive agrega el dialecto hive:// usado por Superset para registrar la conexion
# hacia el Data Warehouse. Se fija version para evitar instalaciones no reproducibles.
RUN pip install --no-cache-dir "PyHive[hive]==0.7.0"

COPY --chown=superset:superset superset_config.py /app/pythonpath/superset_config.py

USER superset
