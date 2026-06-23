# Neo4J - Puntos 5 y 6 con datos reales

Este modulo carga Neo4J desde los datos operacionales del proyecto, usando PostgreSQL, MongoDB o la API FastAPI.

## Flujo

```text
PostgreSQL / MongoDB
        |
        +--> API /graph/export
        |
        +--> neo4j/load_graph.py
                |
                v
              Neo4J
                |
                +--> co-compras, recomendaciones y caminos minimos
                +--> asignacion de rutas con assign_routes.py
```

## Modelo

Nodos:

- `Usuario`: proviene de `users`.
- `Producto`: proviene de `menus`.
- `Pedido`: proviene de `orders`.
- `Restaurante`: proviene de `restaurants`.
- `Ubicacion`: proyeccion analitica desde usuarios y restaurantes reales.
- `Repartidor`: proyeccion operativa desde usuarios disponibles/admin.

Relaciones:

- `(:Usuario)-[:REALIZO]->(:Pedido)`
- `(:Pedido)-[:CONTIENE {cantidad, subtotal}]->(:Producto)`
- `(:Pedido)-[:SALE_DE]->(:Restaurante)`
- `(:Pedido)-[:ENTREGAR_EN]->(:Ubicacion)`
- `(:Usuario)-[:VIVE_EN]->(:Ubicacion)`
- `(:Restaurante)-[:UBICADO_EN]->(:Ubicacion)`
- `(:Repartidor)-[:UBICADO_EN]->(:Ubicacion)`
- `(:Ubicacion)-[:CONECTA_CON {distancia_km, tiempo_minutos}]->(:Ubicacion)`
- `(:Usuario)-[:RECOMIENDA_A]->(:Usuario)`, derivada de compras reales compartidas.
- `(:Repartidor)-[:ASIGNADO_A]->(:Pedido)`, creada por `assign_routes.py`.

Nota: la base actual no tiene columnas de latitud/longitud, repartidores ni tabla de recomendaciones. Por eso esas partes se construyen como proyecciones analiticas a partir de registros reales del sistema.

## Levantar Neo4J

```powershell
docker compose up -d neo4j
```

Abrir:

```text
http://localhost:7474
```

Credenciales por defecto:

```text
Usuario: neo4j
Password: restaurant123
```

## Instalar dependencias locales

```powershell
python -m pip install --user -r .\neo4j\requirements.txt
```

## Cargar desde la API

Primero levantá la API:

```powershell
docker compose up -d api_direct
```

Luego cargá Neo4J:

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_API_URL="http://localhost:8000/graph/export"

python .\neo4j\load_graph.py --source api
```

## Cargar directo desde MongoDB

Como el `.env` usa `DATABASE_ENGINE=mongo`, este modo lee colecciones reales de Mongo:

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_SOURCE="mongo"
$env:GRAPH_MONGO_URL="mongodb://localhost:27017/restaurant_mongo_db"

python .\neo4j\load_graph.py --source mongo
```

## Cargar directo desde PostgreSQL

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_POSTGRES_URL="postgresql+psycopg2://postgres:postgres123@localhost:5432/restaurant_postgres_db"

python .\neo4j\load_graph.py --source postgres
```

Si corrés dentro de Docker y querés usar DNS interno (`postgres`, `mongos`, `neo4j`):

```powershell
$env:NEO4J_USE_DOCKER_DNS="true"
```

## Importante sobre datos reales

El cargador necesita registros en:

```text
users
restaurants
menus
orders
```

Si `order_items` esta vacio, el cargador conecta cada pedido con productos existentes del menu de su restaurante para que el grafo pueda construirse con los datos disponibles actualmente.

## Ejecutar punto 5

Validar grafo, co-compras, recomendaciones y caminos:

```powershell
python .\neo4j\test_neo4j_graph.py
```

Consultas para Neo4J Browser:

```text
neo4j/queries.cypher
```

## Ejecutar punto 6

Asignar pedidos a repartidores con vecino mas cercano:

```powershell
python .\neo4j\assign_routes.py
```

Validar asignaciones:

```powershell
python .\neo4j\test_delivery_routes.py
```

## Evidencias

Capturas recomendadas:

1. `http://localhost:7474` abierto.
2. Resultado de `/graph/export` en la API.
3. Consulta de co-compras.
4. Consulta de usuarios influyentes.
5. Consulta de camino minimo.
6. Salida de `assign_routes.py`.
7. Consulta de `ASIGNADO_A` por repartidor.
