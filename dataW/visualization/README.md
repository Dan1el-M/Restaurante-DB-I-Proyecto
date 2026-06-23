# Visualizacion de Datos - Punto 3

Esta carpeta implementa la capa de visualizacion del proyecto usando Apache Superset como herramienta BI libre.

## Arquitectura implementada

```text
PostgreSQL / MongoDB
        |
API /graph/export
        |
Generador HQL operacional
        |
Apache Hive Data Warehouse
        |
Cubos o vistas OLAP
        |
Apache Superset
        |
Dashboards visuales
```

La herramienta BI no usa APIs intermedias. Superset consulta directamente HiveServer2 y las vistas OLAP del Data Warehouse.

## Servicios Docker

Los servicios quedaron integrados en `docker-compose.yml`:

- `hiveserver2`: servidor Hive del Data Warehouse.
- `warehouse-seed-generator`: consulta la API real y genera `generated/operational_seed.hql`.
- `warehouse-setup`: crea base `restaurant_warehouse`, esquema estrella, carga datos operacionales y vistas OLAP.
- `superset-init`: inicializa Superset y crea el usuario administrador.
- `superset`: interfaz web para construir dashboards.

La imagen de Superset esta pinneada mediante `apache/superset:4.1.2` en `dataW/visualization/superset/Dockerfile`.

## Levantar visualizacion

```powershell
docker compose up -d --build api hiveserver2 warehouse-seed-generator warehouse-setup superset-init superset
```

El servicio `warehouse-seed-generator` toma los datos actuales desde:

```text
http://api/graph/export
```

Por eso los dashboards de Superset quedan basados en los datos existentes de PostgreSQL/MongoDB, no en el archivo antiguo de pruebas.

Luego abrir:

```text
http://localhost:8088
```

Credenciales por defecto:

```text
Usuario: admin
Password: admin
```

Estas credenciales se pueden cambiar con variables de entorno:

- `SUPERSET_ADMIN_USERNAME`
- `SUPERSET_ADMIN_PASSWORD`
- `SUPERSET_ADMIN_EMAIL`
- `SUPERSET_SECRET_KEY`

## Conexion a Hive

La conexion esperada en Superset es:

```text
Nombre: Restaurant Hive Warehouse
SQLAlchemy URI: hive://hive@hiveserver2:10000/restaurant_warehouse?auth=NOSASL
```

El servicio `superset-init` intenta registrar esta conexion automaticamente. Si Superset no la registra por cambios de CLI, crearla manualmente desde:

```text
Settings -> Database Connections -> + Database
```

## Vistas OLAP usadas

- `cubo_ingresos_mes_categoria`
- `cubo_actividad_clientes_zona`
- `cubo_ordenes_completadas_canceladas`
- `cubo_tendencias_horarios_pico`
- `cubo_bestsellers_productos`
- `cubo_lealtad_clientes`

## Dashboards requeridos

Los tres dashboards minimos estan documentados en:

- `dashboards/dashboard_catalog.md`
- `queries/dashboard_01_ingresos_mes_categoria.sql`
- `queries/dashboard_02_actividad_clientes_zona.sql`
- `queries/dashboard_03_ordenes_status.sql`

## Evidencias

Guardar capturas en:

```text
dataW/visualization/evidencias/
```

Capturas recomendadas:

1. Superset abierto en `http://localhost:8088`.
2. Conexion a `Restaurant Hive Warehouse`.
3. Dataset basado en cada vista OLAP.
4. Dashboard 1: ingresos por mes y categoria.
5. Dashboard 2: actividad de clientes por zona.
6. Dashboard 3: ordenes completadas vs canceladas.
