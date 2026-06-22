-- Dashboard 1: Ingresos por mes y categoria de producto
-- Fuente OLAP: cubo_ingresos_mes_categoria
-- Uso en Superset: crear charts de lineas, barras, KPIs y tabla.

SELECT
    year,
    month,
    month_name,
    category,
    total_ordenes,
    total_cantidad_items,
    ingresos_totales,
    promedio_orden,
    ingresos_netos,
    impuestos_totales,
    descuentos_totales
FROM cubo_ingresos_mes_categoria
ORDER BY year, month, category;

-- KPI ingresos totales:
SELECT
    SUM(ingresos_totales) AS kpi_ingresos_totales
FROM cubo_ingresos_mes_categoria;

-- KPI total de ordenes:
SELECT
    SUM(total_ordenes) AS kpi_total_ordenes
FROM cubo_ingresos_mes_categoria;

-- Serie mensual:
SELECT
    year,
    month,
    month_name,
    SUM(ingresos_totales) AS ingresos_mes,
    SUM(total_ordenes) AS ordenes_mes
FROM cubo_ingresos_mes_categoria
GROUP BY year, month, month_name
ORDER BY year, month;

-- Ingresos por categoria:
SELECT
    category,
    SUM(ingresos_totales) AS ingresos_categoria,
    SUM(total_ordenes) AS ordenes_categoria
FROM cubo_ingresos_mes_categoria
GROUP BY category
ORDER BY ingresos_categoria DESC;
