-- Dashboard 2: Actividad de clientes por zona geografica
-- Fuente OLAP: cubo_actividad_clientes_zona
-- Uso en Superset: crear barras por zona, KPIs y tabla geografica.

SELECT
    geographic_zone,
    restaurant_location,
    total_clientes_unicos,
    total_ordenes,
    total_reservaciones,
    ingresos_zona,
    ticket_promedio,
    tamano_promedio_grupo,
    reservaciones_no_show
FROM cubo_actividad_clientes_zona
ORDER BY ingresos_zona DESC, total_ordenes DESC;

-- Actividad por zona:
SELECT
    geographic_zone,
    SUM(total_clientes_unicos) AS clientes_unicos,
    SUM(total_ordenes) AS ordenes,
    SUM(total_reservaciones) AS reservaciones,
    SUM(ingresos_zona) AS ingresos
FROM cubo_actividad_clientes_zona
GROUP BY geographic_zone
ORDER BY ordenes DESC;

-- KPI clientes activos:
SELECT
    SUM(total_clientes_unicos) AS kpi_clientes_activos
FROM cubo_actividad_clientes_zona;

-- Zona con mayor actividad:
SELECT
    geographic_zone,
    SUM(total_ordenes) AS total_ordenes_zona
FROM cubo_actividad_clientes_zona
GROUP BY geographic_zone
ORDER BY total_ordenes_zona DESC
LIMIT 1;

-- Ingresos por ubicacion:
SELECT
    restaurant_location,
    SUM(ingresos_zona) AS ingresos_ubicacion,
    SUM(total_ordenes) AS ordenes_ubicacion
FROM cubo_actividad_clientes_zona
GROUP BY restaurant_location
ORDER BY ingresos_ubicacion DESC;
