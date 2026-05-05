# Carpeta: services/

## Función
Contiene manifiestos para **Deployments** (aplicaciones) y **Services** (exposición de puertos internos).

## Subcarpetas

### `api/` 🔌
- **api-deployment.yaml**: Pod(s) que ejecutan la API FastAPI
- **api-service.yaml**: Expone la API internamente
- Réplicas: 2 (para alta disponibilidad)
- Puerto: 80 (HTTP)

### `keycloak/` 🔐
- **keycloak-deployment.yaml**: Pod que ejecuta Keycloak (autenticación)
- **keycloak-service.yaml**: Expone Keycloak internamente
- Puerto: 8080 (HTTP)
- Administrador y base de datos: Definidos en Secrets

### `search/` 🔍
- **search-deployment.yaml**: Pod(s) que ejecutan el servicio de búsqueda
- **search-service.yaml**: Expone el servicio de búsqueda internamente
- Réplicas: 2 (escalable)
- Puerto: 80 (HTTP)

## Comunicación
```
API ←→ MongoDB, PostgreSQL, Redis, Elasticsearch
Search ←→ MongoDB, Elasticsearch
Keycloak ←→ Base de datos propia
```

## Escalabilidad
- Los Deployments permiten aumentar réplicas:
  ```bash
  kubectl -n restaurante scale deployment api --replicas=3
  ```
