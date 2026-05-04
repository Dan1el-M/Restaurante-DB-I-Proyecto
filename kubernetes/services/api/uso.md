# Carpeta: services/api/

## Función
Manifiestos para la **API FastAPI** - núcleo de la aplicación.

## Archivos

### `api-deployment.yaml`
- **Réplicas**: 2 (por defecto)
- **Imagen**: `restaurante-api:local`
- **Comando**: `uvicorn backend.app.api_main:app --host 0.0.0.0 --port 80`
- **Variables de entorno**:
  - `SERVICE_NAME=api`
  - `ROOT_PATH=/api`
  - Inyecta ConfigMap `restaurante-config` y Secret `restaurante-secret`

### `api-service.yaml`
- **Tipo**: ClusterIP (acceso interno)
- **DNS**: `api.restaurante.svc.cluster.local:80`
- **Puerto**: 80 (HTTP)
- Balanceo de carga automático entre réplicas

## Health Checks
- **readinessProbe**: `/health` cada 10s (después de 10s delay)
- **livenessProbe**: `/health` cada 20s (después de 20s delay)
- Si fallan: Pod se reinicia automáticamente

## Escalado
```bash
# Aumentar a 3 réplicas
kubectl -n restaurante scale deployment api --replicas=3

# Verificar
kubectl -n restaurante get pods
```

## Logs
```bash
kubectl -n restaurante logs -f deployment/api
```
