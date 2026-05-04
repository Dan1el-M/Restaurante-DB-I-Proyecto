# Kubernetes (Mongo simple)

Estos manifiestos levantan el stack en el namespace `restaurante`, usando **MongoDB simple** (1 pod) en lugar del sharding de `docker-compose.yml`.

## Requisitos
- Tener un cluster local (minikube/kind/docker-desktop) con `kubectl`.
- Tener un **Ingress Controller** instalado (por ejemplo NGINX Ingress).
- Tener disponible la imagen de la app en el cluster.

## Secrets (sin passwords alambradas)
Por política del curso, los passwords no se guardan en YAML versionado.

1) Copiar y llenar:
- `kubernetes/secrets/.env.secret.example` → `kubernetes/secrets/.env.secret`

2) El script `kubernetes/_initK8s.ps1` crea el Secret `restaurante-secret` desde ese archivo.

## Imagen de la app (API + Search)
Los deployments `api` y `search` usan la misma imagen (`restaurante-api:local`) y cambian el comando (`api_main` vs `search_main`).

Opciones típicas:
- Publicar la imagen a un registry y cambiar `image:` en:
  - `kubernetes/services/api/api-deployment.yaml`
  - `kubernetes/services/search/search-deployment.yaml`
- En minikube: construir dentro del daemon de minikube y dejar `IfNotPresent`.

## Keycloak realm
El archivo `kubernetes/config/keycloak-realm-configmap.yaml` viene con un placeholder.

Para importar tu realm real (`backend/app/restaurant-realm.json`), lo más limpio es crear el ConfigMap desde archivo:
1) Borrar el configmap placeholder:
   - `kubectl -n restaurante delete configmap keycloak-realm`
2) Crear el configmap desde el JSON:
   - `kubectl -n restaurante create configmap keycloak-realm --from-file=restaurant-realm.json=backend/app/restaurant-realm.json`
3) Reiniciar Keycloak:
   - `kubectl -n restaurante rollout restart deployment keycloak`

## Aplicar manifiestos
- `kubectl apply -f kubernetes/namespaces/`
- `kubectl apply -f kubernetes/config/`
- `kubectl apply -f kubernetes/secrets/`
- `kubectl apply -f kubernetes/storage/`
- `kubectl apply -f kubernetes/databases/`
- `kubectl apply -f kubernetes/services/`
- `kubectl apply -f kubernetes/ingress/`

## URLs esperadas (vía Ingress)
- API Swagger: `/api/docs`
- Search Swagger: `/search/docs`
