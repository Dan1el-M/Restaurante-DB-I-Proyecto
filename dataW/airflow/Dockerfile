ARG AIRFLOW_VERSION=2.10.5-python3.11
FROM apache/airflow:${AIRFLOW_VERSION}

USER root

# curl ayuda a validar servicios HTTP desde tareas y healthchecks.
# El Docker socket se monta desde docker-compose para que los scripts puedan
# invocar contenedores existentes de Hive y Spark sin duplicar tecnologia.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# docker: permite crear el contenedor one-shot de spark-analytics.
# requests: valida Superset/Search/servicios HTTP.
RUN pip install --no-cache-dir \
    "docker==7.1.0" \
    "requests==2.32.3"
