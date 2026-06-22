# Crear dashboards en Superset

Esta guia describe como construir los dashboards del punto 3 desde la interfaz web.

## 1. Entrar a Superset

Abrir:

```text
http://localhost:8088
```

Credenciales por defecto:

```text
admin / admin
```

## 2. Verificar conexion a Hive

Ir a:

```text
Settings -> Database Connections
```

Debe existir:

```text
Restaurant Hive Warehouse
```

Si no existe, crear una conexion nueva con:

```text
SQLAlchemy URI:
hive://hive@hiveserver2:10000/restaurant_warehouse?auth=NOSASL
```

## 3. Registrar datasets

Ir a:

```text
Data -> Datasets -> + Dataset
```

Seleccionar:

```text
Database: Restaurant Hive Warehouse
Schema: restaurant_warehouse
Table:
```

Registrar como minimo:

- `cubo_ingresos_mes_categoria`
- `cubo_actividad_clientes_zona`
- `cubo_ordenes_completadas_canceladas`

Opcionales:

- `cubo_tendencias_horarios_pico`
- `cubo_bestsellers_productos`
- `cubo_lealtad_clientes`

## 4. Crear Dashboard 1

Nombre:

```text
Ingresos por mes y categoria
```

Dataset:

```text
cubo_ingresos_mes_categoria
```

Charts:

- KPI con suma de `ingresos_totales`.
- KPI con suma de `total_ordenes`.
- Line chart con `month_name` en eje X y suma de `ingresos_totales` en eje Y.
- Bar chart con `category` en eje X y suma de `ingresos_totales` en eje Y.
- Table con `year`, `month`, `month_name`, `category`, `total_ordenes`, `ingresos_totales`.

## 5. Crear Dashboard 2

Nombre:

```text
Actividad de clientes por zona geografica
```

Dataset:

```text
cubo_actividad_clientes_zona
```

Charts:

- KPI con suma de `total_clientes_unicos`.
- KPI con suma de `total_ordenes`.
- Bar chart con `geographic_zone` y suma de `total_ordenes`.
- Bar chart con `geographic_zone` y suma de `ingresos_zona`.
- Table con `geographic_zone`, `restaurant_location`, `total_ordenes`, `total_reservaciones`, `ingresos_zona`.

## 6. Crear Dashboard 3

Nombre:

```text
Pedidos completados vs cancelados
```

Dataset:

```text
cubo_ordenes_completadas_canceladas
```

Charts:

- KPI filtrado por completados usando `status_name`.
- KPI filtrado por cancelados usando `status_name`.
- Pie chart o bar chart con `status_name` y suma de `cantidad_ordenes`.
- Line chart con `month_name`, `status_name` y suma de `cantidad_ordenes`.
- Table con `status_name`, `cantidad_ordenes`, `monto_total`, `ticket_promedio`.

## 7. Capturas

Guardar capturas en:

```text
dataW/visualization/evidencias/
```

Estas capturas son la prueba visual de que la herramienta BI consulta las vistas OLAP del Data Warehouse.
