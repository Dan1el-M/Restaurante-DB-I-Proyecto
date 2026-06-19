# Carpeta: services/search/

## Función
Manifiestos para el **servicio de búsqueda** - indexación y búsqueda full-text en Elasticsearch.

## Archivos

### `search-deployment.yaml`
- **Réplicas**: 2 (por defecto)
- **Imagen**: `restaurante-api:local`
- **Comando**: `uvicorn backend.app.search_main:app --host 0.0.0.0 --port 80`
- **Variables de entorno**:
  - `SERVICE_NAME=search`
  - `ROOT_PATH=/search`
  - Inyecta ConfigMap y Secret

### `search-service.yaml`
- **Tipo**: ClusterIP
- **DNS**: `search.restaurante.svc.cluster.local:80`
- **Puerto**: 80 (HTTP)
- Balanceo entre réplicas

## Funcionalidades
- Búsqueda de **restaurantes**
- Búsqueda de **menús** y **platos**
- Búsqueda de **órdenes**
- Filtros y facetas

## Conexiones
```
Search Service
    ↓
Elasticsearch (indexación)
    ↓
MongoDB (obtener datos originales)
```

## Escalabilidad
```bash
# Aumentar búsquedas concurrentes
kubectl -n restaurante scale deployment search --replicas=4
```

## Health Checks
- `/health` cada 10s
- Reinicio automático si falla
