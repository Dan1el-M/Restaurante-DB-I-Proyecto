# Carpeta: ingress/

## Función
Contiene manifiestos de **Ingress** - enrutamiento de tráfico HTTP/HTTPS hacia los servicios internos.

## Archivos

### `restaurante-ingress.yaml`
- Define rutas externas para acceder a los servicios
- Configura:
  - **Host**: `restaurante.local` (o dominio real)
  - **Rutas HTTP**:
    - `/api` → `api-service:80`
    - `/search` → `search-service:80`
    - `/keycloak` → `keycloak-service:8080`

## Requisitos previos
- **Ingress Controller** instalado (NGINX, Traefik, etc.)
- En minikube: `minikube addons enable ingress`
- En Docker Desktop: Activar desde preferences

## Flujo de tráfico
```
Internet (http://restaurante.local/api)
    ↓
Ingress Controller (NGINX)
    ↓
Servicio interno (api-service)
    ↓
Pod API
```

## Antes de usar en producción
- Configurar HTTPS/TLS
- Establecer dominio real (no `restaurante.local`)
- Habilitar autenticación en el Ingress si es necesario
