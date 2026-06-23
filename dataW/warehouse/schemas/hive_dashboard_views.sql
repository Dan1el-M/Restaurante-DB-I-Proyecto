-- Vistas OLAP necesarias para los tres dashboards de Superset.

DROP VIEW IF EXISTS cubo_ingresos_mes_categoria;
CREATE VIEW cubo_ingresos_mes_categoria AS
SELECT
    t.year,
    t.month,
    t.month_name,
    p.category,
    COUNT(DISTINCT fo.order_id) AS total_ordenes,
    SUM(fo.quantity) AS total_cantidad_items,
    SUM(fo.final_amount) AS ingresos_totales,
    AVG(fo.final_amount) AS promedio_orden,
    SUM(fo.net_amount) AS ingresos_netos,
    SUM(fo.tax_amount) AS impuestos_totales,
    SUM(fo.discount) AS descuentos_totales
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
GROUP BY t.year, t.month, t.month_name, p.category;

DROP VIEW IF EXISTS cubo_actividad_clientes_zona;
CREATE VIEW cubo_actividad_clientes_zona AS
SELECT
    dc.geographic_zone,
    dr.location AS restaurant_location,
    COUNT(DISTINCT dc.customer_id) AS total_clientes_unicos,
    COUNT(DISTINCT fo.order_id) AS total_ordenes,
    CAST(0 AS BIGINT) AS total_reservaciones,
    COALESCE(SUM(fo.final_amount), 0) AS ingresos_zona,
    COALESCE(AVG(fo.final_amount), 0) AS ticket_promedio,
    CAST(0 AS DOUBLE) AS tamano_promedio_grupo,
    CAST(0 AS BIGINT) AS reservaciones_no_show
FROM fact_orders fo
INNER JOIN dim_customer dc ON fo.customer_id = dc.customer_id
INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id
GROUP BY dc.geographic_zone, dr.location;

DROP VIEW IF EXISTS cubo_ordenes_completadas_canceladas;
CREATE VIEW cubo_ordenes_completadas_canceladas AS
SELECT
    t.year,
    t.month,
    t.month_name,
    t.quarter,
    ds.status_name,
    COUNT(fo.order_id) AS cantidad_ordenes,
    SUM(fo.final_amount) AS monto_total,
    AVG(fo.final_amount) AS ticket_promedio,
    COUNT(DISTINCT fo.customer_id) AS clientes_unicos,
    COUNT(DISTINCT fo.restaurant_id) AS restaurantes_involucrados
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_status ds ON fo.status_id = ds.status_id
WHERE ds.status_type = 'order'
GROUP BY t.year, t.month, t.month_name, t.quarter, ds.status_name;
