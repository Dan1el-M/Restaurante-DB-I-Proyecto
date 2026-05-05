# Carpeta: databases/postgres/

## Función
Manifiestos para **PostgreSQL** - base de datos relacional SQL.

## Archivos

### `postgres-deployment.yaml`
- Define el pod que ejecuta PostgreSQL
- Configura:
  - Imagen: `postgres:latest`
  - Puerto: 5432 (puerto estándar PostgreSQL)
  - Variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - Volumen persistente para datos

### `postgres-service.yaml`
- Expone PostgreSQL como servicio interno
- DNS: `postgres.restaurante.svc.cluster.local:5432`
- Acceso: Solo desde dentro del namespace `restaurante`

## Almacenamiento
- **Volumen**: `postgres-pvc` (10Gi) en `storage/`
- Estructura de datos: Definida en `dbs/postgres/db_postgres.sql`

## Uso en el proyecto
- Almacenamiento de datos estructurados y transaccionales
- Posible uso para auditoría, logs o datos que requieran ACID strict

## Credenciales
- Usuario/contraseña: Definidos en `secrets/restaurante-secret.yaml`
- Base de datos default: `restaurante`
