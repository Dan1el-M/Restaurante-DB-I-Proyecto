# Carpeta: databases/

## Función
Contiene manifiestos de Kubernetes para **todas las bases de datos y servicios de almacenamiento** del proyecto.

## Subcarpetas

### `elasticsearch/` 📊
- **elasticsearch-deployment.yaml**: Pod que ejecuta Elasticsearch (búsqueda full-text)
- **elasticsearch-service.yaml**: Expone Elasticsearch internamente en el cluster
- Usado por el servicio de Search para indexación y búsquedas

### `mongo/` 🍃
- **mongo-statefulset.yaml**: MongoDB de replica única (no sharding)
- **mongo-service.yaml**: Expone MongoDB internamente
- Base de datos principal para documentos (usuarios, órdenes, reservaciones)

### `postgres/` 🐘
- **postgres-deployment.yaml**: PostgreSQL para datos relacionales
- **postgres-service.yaml**: Expone PostgreSQL internamente
- Usado para datos estructurados y transacciones ACID

### `redis/` ⚡
- **redis-deployment.yaml**: Redis para caché y sesiones
- **redis-service.yaml**: Expone Redis internamente
- Mejora la performance cacheando datos frecuentes

## Persistencia
- Los volúmenes se definen en `../storage/` (PersistentVolumeClaims)
- Cada base de datos retiene datos incluso cuando los pods se reinician
