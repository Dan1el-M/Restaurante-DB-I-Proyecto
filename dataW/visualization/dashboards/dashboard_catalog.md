# Catalogo de Dashboards OLAP

Este catalogo define los dashboards que se deben crear en Superset para cumplir el punto 3.

## Dashboard 1: Ingresos por mes y categoria

**Fuente OLAP:** `cubo_ingresos_mes_categoria`

**Objetivo:** visualizar la evolucion de ingresos y ordenes por mes y categoria de producto.

**Charts recomendados:**

- KPI: suma de `ingresos_totales`.
- KPI: suma de `total_ordenes`.
- Line chart: `ingresos_totales` por `year`, `month_name`.
- Bar chart agrupado: `ingresos_totales` por `category`.
- Tabla: `year`, `month`, `month_name`, `category`, `total_ordenes`, `ingresos_totales`, `promedio_orden`.

**Preguntas que responde:**

- Que categorias generan mas ingresos.
- En que mes se vendio mas.
- Como cambian las ventas por categoria.

## Dashboard 2: Actividad de clientes por zona geografica

**Fuente OLAP:** `cubo_actividad_clientes_zona`

**Objetivo:** comparar actividad de clientes, ordenes, reservaciones e ingresos por zona.

**Charts recomendados:**

- KPI: suma de `total_clientes_unicos`.
- KPI: suma de `total_ordenes`.
- Bar chart: `total_ordenes` por `geographic_zone`.
- Bar chart: `total_clientes_unicos` por `geographic_zone`.
- Tabla: `geographic_zone`, `restaurant_location`, `total_ordenes`, `total_reservaciones`, `ingresos_zona`.

**Preguntas que responde:**

- Que zona tiene mas actividad.
- En que ubicacion hay mas pedidos.
- Que zonas generan mas ingresos.

## Dashboard 3: Pedidos completados vs cancelados

**Fuente OLAP:** `cubo_ordenes_completadas_canceladas`

**Objetivo:** analizar el comportamiento de ordenes por estado y su impacto en ingresos.

**Charts recomendados:**

- KPI: ordenes completadas.
- KPI: ordenes canceladas.
- KPI: tasa de cancelacion.
- Pie chart o bar chart: `cantidad_ordenes` por `status_name`.
- Line chart: `cantidad_ordenes` por `year`, `month_name`, `status_name`.
- Tabla: `status_name`, `cantidad_ordenes`, `porcentaje_ordenes`, `monto_total`, `ticket_promedio`.

**Preguntas que responde:**

- Cuantos pedidos se completan.
- Cuantos pedidos se cancelan.
- Cual es la tasa de cancelacion.
- Que impacto tienen las cancelaciones en los ingresos.

## Dashboards extra sugeridos

### Horarios pico

**Fuente OLAP:** `cubo_tendencias_horarios_pico`

- Ordenes por hora.
- Ingresos por hora.
- Comparacion por dia de la semana.

### Productos mas vendidos

**Fuente OLAP:** `cubo_bestsellers_productos`

- Top 10 productos por ingresos.
- Top 10 productos por cantidad vendida.
- Ranking por categoria.

### Lealtad de clientes

**Fuente OLAP:** `cubo_lealtad_clientes`

- Clientes con mas ordenes.
- Clientes con mas reservaciones.
- Clientes con mayor gasto.
