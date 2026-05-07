# Kubernetes (Mongo simple)

Estos manifiestos levantan el stack en el namespace `restaurante`, usando **MongoDB simple** (1 pod) en lugar del sharding de `docker-compose.yml`.

## Requisitos
- Tener un cluster local (minikube/kind/docker-desktop) con `kubectl`.
- Tener un **Ingress Controller** instalado (por ejemplo NGINX Ingress).
- Tener disponible la imagen de la app en el cluster.

## Configuracion con `.env`
El `.env` de la raiz es la fuente principal de configuracion para el proyecto:
- Docker Compose lo lee automaticamente.
- La app Python lo carga con `python-dotenv` cuando corre localmente.
- `kubernetes/_initK8s.ps1` lo lee y crea/actualiza `restaurante-config` y `restaurante-secret`.

Las variables sensibles no quedan quemadas en YAML. El init separa passwords, secrets, tokens y `POSTGRES_URL` en el Secret de Kubernetes.

Opcionalmente podes crear `kubernetes/secrets/.env.secret` para sobreescribir solo secretos locales sin cambiar `.env`.

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

## Si el Ingress no funciona
Si `kubectl -n restaurante get ingress` muestra `ADDRESS` vacío, te falta instalar un **Ingress Controller** (por ejemplo NGINX Ingress) o configurar un IngressClass por defecto.

Si el cluster quedo con el webhook `ingress-nginx-admission` pero sin el service `ingress-nginx-controller-admission`, `kubernetes/_initK8s.ps1` omite Ingress y deja funcionando los servicios LoadBalancer. Para reparar Ingress:
- `powershell -ExecutionPolicy Bypass -File kubernetes/_installIngressNginx.ps1`

Si no queres usar Ingress, podes poner `K8S_APPLY_INGRESS=false` en `.env`.

Como alternativa inmediata podés usar port-forward:
- API: `kubectl -n restaurante port-forward svc/api 8080:80` → `http://localhost:8080/api/docs`
- Search: `kubectl -n restaurante port-forward svc/search 8081:80` → `http://localhost:8081/search/docs`
- Keycloak: `kubectl -n restaurante port-forward svc/keycloak 8001:8080` → `http://localhost:8001/admin/master/console/`

## Instalar NGINX Ingress Controller (Docker Desktop)
Ejecutá:
- `powershell -ExecutionPolicy Bypass -File kubernetes/_installIngressNginx.ps1`

## Exponer URLs con puertos (sin port-forward)
En Docker Desktop, podés exponer servicios con `type: LoadBalancer` y acceder por `localhost`.
Este repo incluye:
- `kubernetes/services/api/api-lb-service.yaml` → `http://localhost:8080/api/docs`
- `kubernetes/services/search/search-lb-service.yaml` → `http://localhost:8081/search/docs`
- `kubernetes/services/keycloak/keycloak-lb-service.yaml` → `http://localhost:8001/admin/master/console/`
