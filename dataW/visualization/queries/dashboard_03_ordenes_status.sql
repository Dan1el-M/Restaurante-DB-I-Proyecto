-- Dashboard 3: Pedidos completados vs cancelados
-- Fuente OLAP: cubo_ordenes_completadas_canceladas
-- Uso en Superset: crear pastel/barras por estado, serie temporal, KPIs y tabla.

SELECT
    year,
    month,
    month_name,
    quarter,
    status_name,
    cantidad_ordenes,
    monto_total,
    ticket_promedio,
    clientes_unicos,
    restaurantes_involucrados
FROM cubo_ordenes_completadas_canceladas
ORDER BY year, month, status_name;

-- Distribucion general por estado:
SELECT
    status_name,
    SUM(cantidad_ordenes) AS total_ordenes,
    SUM(monto_total) AS ingresos_asociados,
    ROUND(
        SUM(cantidad_ordenes) * 100.0
        / SUM(SUM(cantidad_ordenes)) OVER (),
        2
    ) AS porcentaje_ordenes
FROM cubo_ordenes_completadas_canceladas
GROUP BY status_name
ORDER BY total_ordenes DESC;

-- Serie temporal por estado:
SELECT
    year,
    month,
    month_name,
    status_name,
    SUM(cantidad_ordenes) AS ordenes_mes_estado,
    SUM(monto_total) AS ingresos_mes_estado
FROM cubo_ordenes_completadas_canceladas
GROUP BY year, month, month_name, status_name
ORDER BY year, month, status_name;

-- KPI pedidos completados:
SELECT
    SUM(cantidad_ordenes) AS kpi_pedidos_completados
FROM cubo_ordenes_completadas_canceladas
WHERE LOWER(status_name) LIKE '%complet%';

-- KPI pedidos cancelados:
SELECT
    SUM(cantidad_ordenes) AS kpi_pedidos_cancelados
FROM cubo_ordenes_completadas_canceladas
WHERE LOWER(status_name) LIKE '%cancel%';

-- KPI tasa de cancelacion:
SELECT
    ROUND(
        SUM(CASE WHEN LOWER(status_name) LIKE '%cancel%' THEN cantidad_ordenes ELSE 0 END) * 100.0
        / SUM(cantidad_ordenes),
        2
    ) AS tasa_cancelacion
FROM cubo_ordenes_completadas_canceladas;
