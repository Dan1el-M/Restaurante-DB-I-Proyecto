# Neo4J - Puntos 5 y 6 con datos reales

Este modulo carga Neo4J desde los datos operacionales del proyecto y completa el Punto 6 con asignacion de rutas de entrega.

## Revision inicial

Antes de completar el Punto 6 se reviso el repositorio y ya existia una base relacionada con Neo4J y entregas:

- `neo4j/load_graph.py`: carga usuarios, productos, pedidos, restaurantes, ubicaciones, conexiones entre ubicaciones y repartidores proyectados.
- `neo4j/assign_routes.py`: asignaba pedidos a repartidores usando rutas calculadas en Neo4J.
- `neo4j/test_delivery_routes.py`: validaba relaciones `ASIGNADO_A`.
- `neo4j/queries.cypher`: tenia consultas de Punto 5 y un resumen inicial de Punto 6.
- `dataW/airflow/dags/restaurant_olap_pipeline.py`: orquesta los puntos de warehouse, Spark, Hive y Search.

Decision: se reutilizo la implementacion Neo4J existente y se completo con carga desde fuentes operacionales, consultas Cypher separadas, mejor salida de validacion y una tarea opcional de Airflow apagada por defecto.

## Archivos

Agregados:

- `neo4j/delivery_assignment.py`: validador local de la heuristica de vecino mas cercano, usado solo como respaldo cuando Neo4J no esta disponible.
- `neo4j/sample_delivery_data.json`: datos controlados para validar la heuristica fuera de Docker; no reemplazan el flujo principal con Neo4J.
- `neo4j/delivery_assignment_queries.cypher`: consultas Cypher especificas del Punto 6.

Modificados:

- `neo4j/assign_routes.py`: imprime checklist completo, totales por repartidor y documenta funciones clave.
- `dataW/airflow/dags/restaurant_olap_pipeline.py`: agrega validacion opcional del Punto 6.
- `docker-compose.yml`: monta `./neo4j` dentro de Airflow y agrega variables opcionales.
- `dataW/airflow/README_AIRFLOW.md`: documenta la tarea opcional.

## Modelo usado

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

La base operacional actual no tiene columnas reales de latitud/longitud ni una tabla de repartidores. Por eso `load_graph.py` crea ubicaciones y repartidores como proyecciones analiticas desde usuarios, restaurantes y pedidos reales.

## Algoritmo

El Punto 6 usa vecino mas cercano:

1. Cada repartidor inicia en su ubicacion actual, normalmente un restaurante.
2. Se consultan los pedidos entregables con restaurante de salida y ubicacion de cliente.
3. Para cada repartidor se evalua cada pedido pendiente.
4. Si el pedido sale del restaurante base del repartidor, se asume que va precargado y se calcula la ruta desde la ubicacion actual hasta el cliente.
5. Si el pedido sale de otro restaurante, se calcula desplazamiento hasta ese restaurante + entrega al cliente.
6. Se elige el pedido con menor tiempo total.
7. El repartidor actualiza su ubicacion al ultimo cliente visitado.
8. Se repite por rondas hasta agotar pedidos o capacidad.
9. Se persiste `ASIGNADO_A` con orden, ruta, distancia, tiempo y heuristica.

## Validacion local de respaldo

El flujo principal del Punto 5 y Punto 6 usa datos operacionales cargados en Neo4J desde `/graph/export`. Esta validacion local no necesita Docker y sirve unicamente como respaldo para explicar la heuristica si Neo4J no esta disponible durante una demo:

```powershell
python .\neo4j\delivery_assignment.py
```

Salida esperada:

```text
[OK] Se cargaron repartidores disponibles.
[OK] Se cargaron pedidos pendientes con ubicacion.
[OK] Se calculo la distancia entre ubicaciones.
[OK] Se aplico algoritmo de vecino mas cercano.
[OK] Se asignaron pedidos a repartidores.
[OK] Se generaron rutas optimizadas.
[OK] Se calculo distancia total por repartidor.
[OK] Se calculo tiempo estimado por ruta.
[OK] Punto 6 validado correctamente.
```

Tambien imprime rutas como:

```text
Repartidor: Carlos
Ruta: Restaurante TEC -> Cartago Centro -> Paraiso
Pedidos asignados: [101, 104]
Distancia total: 7.73 km
Tiempo estimado: 30 min
```

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

## Cargar grafo real

Desde la API:

```powershell
docker compose up -d api_direct neo4j

$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_API_URL="http://localhost:8000/graph/export"

python .\neo4j\load_graph.py --source api
```

Desde MongoDB:

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_SOURCE="mongo"
$env:GRAPH_MONGO_URL="mongodb://localhost:27017/restaurant_mongo_db"

python .\neo4j\load_graph.py --source mongo
```

Desde PostgreSQL:

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="restaurant123"
$env:GRAPH_POSTGRES_URL="postgresql+psycopg2://postgres:postgres123@localhost:5432/restaurant_postgres_db"

python .\neo4j\load_graph.py --source postgres
```

## Ejecutar Punto 5

```powershell
python .\neo4j\test_neo4j_graph.py
```

Consultas para Neo4J Browser:

```text
neo4j/queries.cypher
```

## Ejecutar Punto 6 con Neo4J

Asignar pedidos a repartidores:

```powershell
python .\neo4j\assign_routes.py
```

Validar asignaciones persistidas:

```powershell
python .\neo4j\test_delivery_routes.py
```

Consultas para capturas:

```text
neo4j/delivery_assignment_queries.cypher
```

## Integracion con Airflow

El DAG `restaurant_olap_pipeline` incluye la tarea `validate_delivery_routes_optional`. Por defecto no ejecuta el Punto 6 para no acoplar el pipeline OLAP a Neo4J.

Para activarla:

```powershell
$env:ENABLE_DELIVERY_ROUTE_VALIDATION="true"
docker compose up -d --build airflow-init airflow-webserver airflow-scheduler
```

La tarea ejecuta:

```text
/opt/airflow/neo4j/delivery_assignment.py
```

## Evidencia recomendada

Para la entrega o video:

1. Levantar Neo4J y cargar datos operacionales con `load_graph.py --source api`.
2. Ejecutar `python .\neo4j\test_neo4j_graph.py` para validar el Punto 5.
3. Ejecutar `python .\neo4j\assign_routes.py` para asignar rutas sobre el grafo.
4. Ejecutar `python .\neo4j\test_delivery_routes.py` para validar asignaciones persistidas.
5. Abrir Neo4J Browser y correr `neo4j/queries.cypher` y `neo4j/delivery_assignment_queries.cypher`.
6. Opcional: ejecutar `python .\neo4j\delivery_assignment.py` como validacion local de respaldo de la heuristica.
7. Mostrar en Airflow que la tarea opcional existe y puede ejecutar la validacion local sin afectar el flujo OLAP.

## Supuestos

- Las distancias se estiman desde coordenadas derivadas porque la base operacional actual no almacena latitud/longitud real.
- Los repartidores se derivan de usuarios/admin disponibles para no crear una tabla operacional nueva.
- La heuristica es intencionalmente simple y explicable: vecino mas cercano con capacidad por repartidor.
- Si Neo4J no esta disponible, `delivery_assignment.py` permite validar la heuristica localmente como respaldo, pero la evidencia principal debe salir de `load_graph.py`, `assign_routes.py` y las consultas Cypher.
