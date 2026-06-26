# Punto 4 - Orquestacion con Apache Airflow

Esta carpeta implementa Apache Airflow como orquestador del pipeline analitico del proyecto.

## Arquitectura

```text
PostgreSQL / MongoDB
        |
Airflow DAG: restaurant_olap_pipeline
        |
Spark transformations
        |
Hive Data Warehouse
        |
Validacion de cubos OLAP
        |
Reindexado Search / Elasticsearch si cambia catalogo
        |
Superset consulta vistas OLAP
```

Airflow no reemplaza Hive, Spark ni Superset. Solo coordina la ejecucion y validacion del flujo.

## Servicios agregados

- `airflow-postgres`: base de metadatos de Airflow.
- `airflow-init`: migra la base de Airflow y crea usuario admin.
- `airflow-webserver`: UI de Airflow.
- `airflow-scheduler`: ejecuta DAGs y tareas.

La imagen custom esta en:

```text
dataW/airflow/Dockerfile
```

Usa version pinneada:

```text
apache/airflow:2.10.5-python3.11
```

## Levantar Airflow

```powershell
docker compose up -d --build airflow-init airflow-webserver airflow-scheduler
```

Este comando tambien levanta dependencias necesarias:

- `airflow-postgres`
- `hiveserver2`
- `warehouse-setup`
- `spark-master`
- `spark-worker`

## Acceso web

```text
http://localhost:8090
```

Credenciales por defecto:

```text
Usuario: admin
Password: admin
```

Variables configurables:

- `AIRFLOW_PORT`: puerto local del webserver. Default: `8090`.
- `AIRFLOW_ADMIN_USERNAME`: usuario admin. Default: `admin`.
- `AIRFLOW_ADMIN_PASSWORD`: password admin. Default: `admin`.
- `AIRFLOW_ADMIN_EMAIL`: correo admin. Default: `admin@example.com`.
- `ALLOW_SOURCE_UNAVAILABLE`: permite continuar si Postgres/Mongo no estan levantados. Default: `true`.
- `FORCE_REINDEX_PRODUCTS`: fuerza reindexado de productos. Default: `false`.
- `REINDEX_ON_FIRST_RUN`: reindexa en la primera corrida del DAG. Default: `false`.
- `ALLOW_REINDEX_UNAVAILABLE`: permite continuar si Search requiere auth o no esta arriba. Default: `true`.
- `SEARCH_REINDEX_URL`: endpoint Docker para reindex. Default: `http://search/reindex`.
- `SEARCH_AUTH_TOKEN`: token Bearer opcional para reindexado.
- `ENABLE_DELIVERY_ROUTE_VALIDATION`: ejecuta la validacion local del Punto 6 dentro del DAG. Default: `false`.
- `AIRFLOW_POINT6_SCRIPT`: ruta del script de rutas dentro del contenedor. Default: `/opt/airflow/neo4j/delivery_assignment.py`.

## DAG principal

Nombre exacto:

```text
restaurant_olap_pipeline
```

Archivo:

```text
dataW/airflow/dags/restaurant_olap_pipeline.py
```

Schedule:

```text
@daily
```

Tags:

```text
olap, airflow, spark, hive, restaurant
```

## Flujo del DAG

```text
start
  -> extract_from_source
  -> run_spark_transformations
  -> load_to_data_warehouse
  -> validate_warehouse
  -> validate_delivery_routes_optional
  -> check_product_catalog_changes
  -> reindex_elasticsearch_if_needed / skip_reindex
  -> finish
```

## Que hace cada tarea

- `extract_from_source`: valida conectividad a Postgres/Mongo. Si no estan arriba, puede continuar con `ALLOW_SOURCE_UNAVAILABLE=true`.
- `run_spark_transformations`: ejecuta el job PySpark existente del punto 2 usando el cluster Spark del compose.
- `load_to_data_warehouse`: crea/actualiza schema, seed y vistas OLAP en Hive. Evita duplicar seed si `fact_orders` ya tiene datos.
- `validate_warehouse`: ejecuta consultas reales en Hive para validar hechos y cubos OLAP.
- `validate_delivery_routes_optional`: por defecto solo registra skip; con `ENABLE_DELIVERY_ROUTE_VALIDATION=true` ejecuta una validacion local de respaldo para la heuristica del Punto 6.
- `check_product_catalog_changes`: calcula hash de `dim_product` y decide si cambio el catalogo.
- `reindex_elasticsearch_if_needed`: llama `POST http://search/reindex` si el catalogo cambio o si se fuerza.
- `skip_reindex`: rama limpia si no hay cambios de catalogo.

## Ejecutar manualmente

1. Entrar a `http://localhost:8090`.
2. Buscar `restaurant_olap_pipeline`.
3. Activar el toggle del DAG si aparece pausado.
4. Clic en el boton de play.
5. Seleccionar `Trigger DAG`.

## Revisar Graph View

1. Abrir el DAG.
2. Ir a `Graph`.
3. Validar que las tareas aparezcan conectadas en orden.

## Revisar Grid View

1. Abrir el DAG.
2. Ir a `Grid`.
3. Validar que la corrida manual termine en `success`.
4. La tarea `skip_reindex` o `reindex_elasticsearch_if_needed` puede aparecer como `skipped` segun el branch.

## Revisar logs

1. En `Grid`, abrir una tarea.
2. Clic en `Logs`.
3. Buscar mensajes como:

```text
Executing point 4 script
SPARK ORCHESTRATION COMPLETED
DATA WAREHOUSE LOAD COMPLETED
WAREHOUSE VALIDATION COMPLETED
CATALOG_CHANGED=true/false
```

## Validar Hive despues del DAG

```powershell
docker exec -it hiveserver2 /opt/hive/bin/beeline -u "jdbc:hive2://localhost:10000/restaurant_warehouse" -e "SELECT COUNT(*) FROM fact_orders; SELECT * FROM cubo_ingresos_mes_categoria LIMIT 5;"
```

## Validar Superset

Abrir:

```text
http://localhost:8088
```

Luego probar en SQL Lab:

```sql
SELECT * FROM cubo_ingresos_mes_categoria LIMIT 5;
```

## Validar Punto 6 desde Airflow

El flujo principal del Punto 6 se valida con Neo4J usando `load_graph.py --source api`, `assign_routes.py` y `test_delivery_routes.py`. La tarea opcional de Airflow ejecuta `neo4j/delivery_assignment.py` como respaldo local para dejar evidencia de la heuristica dentro del DAG sin acoplar el pipeline OLAP a Neo4J:

```powershell
$env:ENABLE_DELIVERY_ROUTE_VALIDATION="true"
docker compose up -d --build airflow-init airflow-webserver airflow-scheduler
```

En los logs de `validate_delivery_routes_optional` deben verse mensajes `[OK]` de repartidores, pedidos, vecino mas cercano, rutas y tiempos.

## Prueba automatizada

Desde la raiz del proyecto:

```powershell
python dataW\airflow\test\test_airflow_point4_requirements.py
```

La prueba imprime un checklist completo y termina con codigo `0` solo si todos los requisitos pasan.
