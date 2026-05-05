# Carpeta: databases/redis/

## Función
Manifiestos para **Redis** - almacenamiento en caché y sesiones en memoria.

## Archivos

### `redis-deployment.yaml`
- Define el pod que ejecuta Redis
- Configura:
  - Imagen: `redis:latest`
  - Puerto: 6379 (puerto estándar Redis)
  - Volumen persistente (AOF o RDB)
  - Sin autenticación por defecto (en red privada)

### `redis-service.yaml`
- Expone Redis como servicio interno
- DNS: `redis.restaurante.svc.cluster.local:6379`
- Acceso: Solo desde dentro del namespace `restaurante`

## Usado por
- **API**: Cache de datos de consultas frecuentes
- **cache_service.py**: Servicio de caché en `backend/app/cache/`
- Sesiones de usuario y tokens

## Beneficios
- Mejora performance al evitar consultas repetidas a la BD
- Almacenamiento temporal de datos
- Sesiones de usuario con TTL (Time To Live)

## Persistencia
- AOF (Append-Only File): Registra todas las operaciones
- Permite recuperar datos si el pod se reinicia
