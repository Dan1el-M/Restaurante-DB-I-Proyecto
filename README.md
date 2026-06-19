# Restaurante-DB-I-Proyecto

API REST para gestion de restaurantes, reservas, menus y usuarios. El proyecto incluye FastAPI, autenticacion con Keycloak, PostgreSQL, MongoDB shardeado, Redis, Elasticsearch, Nginx y scripts para Docker Compose y Kubernetes.

## Requisitos

- Docker Desktop con Docker Compose.
- Kubernetes
- PowerShell en Windows.
- Puertos: `5432`, `6379`, `8000`, `8001`, `8080`, `9200`, `27017`.

## Configuracion principal

El archivo `.env` de la raiz es la fuente principal de configuracion para Docker Compose, la app local y el init de Kubernetes.

Variables mas importantes:

- `DATABASE_ENGINE=mongo` usa MongoDB.
- `DATABASE_ENGINE=postgres` usa PostgreSQL.
- `KEYCLOAK_URL=http://keycloak:8080` se usa dentro de Docker Compose.
- `KEYCLOAK_PORT=8001` expone Keycloak en `http://localhost:8001`.
- `NGINX_PORT=8080` expone API y Search por Nginx.
- `API_PORT=8000` expone la API directa.

Para pruebas ejecutadas desde Windows, los fixtures de integracion convierten URLs internas como `http://keycloak:8080` a `localhost` cuando hace falta.

## Ejecutar Todo Con Docker Compose

1. Levantar el stack completo:

```powershell
docker compose up -d --build
```

2. Verificar que los contenedores esten vivos:

```powershell
docker compose ps
```

3. Revisar logs si algo tarda en arrancar:

```powershell
docker compose logs -f keycloak
docker compose logs -f api
docker compose logs -f seed
```

Keycloak puede tardar varios minutos en el primer arranque porque importa el realm. Espera hasta ver un mensaje parecido a `Keycloak ... started` antes de correr pruebas de integracion.

## URLs Locales

- API por Nginx: `http://localhost:8080/api/docs`
- Search por Nginx: `http://localhost:8080/search/docs`
- API directa: `http://localhost:8000/docs`
- Keycloak Admin: `http://localhost:8001/admin/master/console/`
- Elasticsearch: `http://localhost:9200`
- MongoDB: `mongodb://localhost:27017`
- PostgreSQL: `localhost:5432`

Credenciales por defecto desde `.env`:

- Keycloak admin: `admin` / `admin`
- Usuario seed de la app: `admin` / `admin`
- PostgreSQL: `postgres` / `postgres123`

## Seed Del Admin

El servicio `seed` crea o actualiza el usuario admin en Keycloak y en la base activa.

Para ejecutarlo de nuevo:

```powershell
docker compose run --rm seed
```

Si Keycloak no esta listo, el seed espera y muestra progreso. Los tiempos se controlan con:

- `SEED_WAIT_SECONDS`
- `SEED_WAIT_RETRIES`
- `SEED_WAIT_DELAY_SECONDS`

## Cambiar Motor De Base De Datos

La API usa un solo motor activo a la vez. Se controla con `DATABASE_ENGINE` en `.env`.

### Usar MongoDB

1. Editar `.env`:

```env
DATABASE_ENGINE=mongo
MONGO_URL=mongodb://mongos:27017/restaurant_mongo_db
```

2. Recrear API, Search y Seed para que tomen la nueva variable:

```powershell
docker compose up -d --build api api_direct search seed
```

3. Ejecutar seed:

```powershell
docker compose run --rm seed
```

MongoDB en Docker Compose corre como cluster shardeado:

- Config Server Replica Set: `cfgReplSet`
- Shard 1 Replica Set: `shard1ReplSet`
- Router: `mongos`

La API se conecta siempre al router `mongos`.

### Usar PostgreSQL

1. Editar `.env`:

```env
DATABASE_ENGINE=postgres
POSTGRES_URL=postgresql+psycopg2://postgres:postgres123@postgres:5432/restaurant_postgres_db
```

2. Recrear API, Search y Seed:

```powershell
docker compose up -d --build api api_direct search seed
```

3. Ejecutar seed:

```powershell
docker compose run --rm seed
```

PostgreSQL ejecuta los scripts de `dbs/postgres/` solo cuando el volumen `postgres_data` esta vacio. Si cambiaste el schema y necesitas reinicializar desde cero, baja el stack con volumenes:

```powershell
docker compose down -v
docker compose up -d --build
```

Eso borra datos locales de Docker.

## Pruebas

### Unitarias

```powershell
pytest backend/tests/unit
```

### Integracion

Primero levanta el stack:

```powershell
docker compose up -d --build
```

Espera a que Keycloak responda:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8001/realms/master
```

Luego corre:

```powershell
pytest backend/tests/integration
```

El timeout de espera para servicios externos se controla con:

```env
INTEGRATION_SERVICE_TIMEOUT_SECONDS=900
```

### Coverage Completo

`pytest.ini` exige 90% de coverage:

```powershell
pytest
```

Si los servicios de integracion no estan listos, pytest puede fallar antes de ejecutar los tests y el coverage baja artificialmente. En ese caso revisa primero:

```powershell
docker compose ps
docker compose logs keycloak --tail 120
docker compose logs seed --tail 120
```

## Kubernetes Local

El init de Kubernetes tambien lee `.env`:

```powershell
powershell -ExecutionPolicy Bypass -File kubernetes/_initK8s.ps1
```

URLs esperadas por LoadBalancer:

- `http://localhost:8080/api/docs`
- `http://localhost:8081/search/docs`
- `http://localhost:8001/admin/master/console/`

Si queres usar Ingress, instala el controller:

```powershell
powershell -ExecutionPolicy Bypass -File kubernetes/_installIngressNginx.ps1
```

Si no queres aplicar Ingress:

```env
K8S_APPLY_INGRESS=false
```

## Despliegue Con Imagen Publicada

Para usar la imagen publicada en GHCR:

```powershell
docker login ghcr.io
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Opcionalmente define otra imagen:

```powershell
$env:API_IMAGE="ghcr.io/dan1el-m/restaurante-db-i-proyecto:main"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Limpieza

Detener contenedores sin borrar datos:

```powershell
docker compose down
```

Borrar contenedores y volumenes locales:

```powershell
docker compose down -v
```
