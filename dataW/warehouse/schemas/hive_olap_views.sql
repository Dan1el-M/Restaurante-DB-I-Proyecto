-- =====================================================
-- VISTAS OLAP - CUBOS DE ANALISIS PARA HIVE
-- Base de Datos II - Proyecto OLAP
-- =====================================================

-- =====================================================
-- CUBO 1: INGRESOS POR MES Y CATEGORIA DE PRODUCTO
-- =====================================================
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

-- =====================================================
-- CUBO 2: ACTIVIDAD DE CLIENTES POR ZONA GEOGRAFICA
-- =====================================================
DROP VIEW IF EXISTS cubo_actividad_clientes_zona;

CREATE VIEW cubo_actividad_clientes_zona AS
SELECT
    activity.geographic_zone,
    activity.restaurant_location,
    COUNT(DISTINCT activity.customer_id) AS total_clientes_unicos,
    COUNT(DISTINCT activity.order_id) AS total_ordenes,
    COUNT(DISTINCT activity.reservation_id) AS total_reservaciones,
    COALESCE(SUM(activity.final_amount), 0) AS ingresos_zona,
    COALESCE(AVG(activity.final_amount), 0) AS ticket_promedio,
    COALESCE(AVG(activity.party_size), 0) AS tamano_promedio_grupo,
    SUM(CASE WHEN activity.no_show = true THEN 1 ELSE 0 END) AS reservaciones_no_show
FROM (
    SELECT
        dc.customer_id,
        dc.geographic_zone,
        dr.location AS restaurant_location,
        fo.order_id,
        CAST(NULL AS INT) AS reservation_id,
        fo.final_amount,
        CAST(NULL AS INT) AS party_size,
        CAST(false AS BOOLEAN) AS no_show
    FROM fact_orders fo
    INNER JOIN dim_customer dc ON fo.customer_id = dc.customer_id
    INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id

    UNION ALL

    SELECT
        dc.customer_id,
        dc.geographic_zone,
        dr.location AS restaurant_location,
        CAST(NULL AS INT) AS order_id,
        fr.reservation_id,
        CAST(NULL AS DOUBLE) AS final_amount,
        fr.party_size,
        fr.no_show
    FROM fact_reservations fr
    INNER JOIN dim_customer dc ON fr.customer_id = dc.customer_id
    INNER JOIN dim_restaurant dr ON fr.restaurant_id = dr.restaurant_id
) activity
GROUP BY activity.geographic_zone, activity.restaurant_location;

-- =====================================================
-- CUBO 3: ORDENES COMPLETADAS VS CANCELADAS
-- =====================================================
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

-- =====================================================
-- CUBO 4: TENDENCIAS DE CONSUMO - HORARIOS PICO
-- =====================================================
DROP VIEW IF EXISTS cubo_tendencias_horarios_pico;

CREATE VIEW cubo_tendencias_horarios_pico AS
SELECT
    t.day_name,
    t.month_name,
    CAST(HOUR(fo.order_time) AS INT) AS hora,
    p.category,
    COUNT(fo.order_id) AS ordenes_por_hora,
    SUM(fo.quantity) AS items_vendidos,
    SUM(fo.final_amount) AS ingresos_hora,
    AVG(fo.final_amount) AS ticket_promedio,
    COUNT(DISTINCT fo.customer_id) AS clientes_unicos
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
WHERE fo.order_time IS NOT NULL
GROUP BY t.day_name, t.month_name, HOUR(fo.order_time), p.category;

-- =====================================================
-- CUBO 5: CRECIMIENTO MENSUAL Y ANALISIS COMPARATIVO
-- =====================================================
DROP VIEW IF EXISTS cubo_crecimiento_mensual;

CREATE VIEW cubo_crecimiento_mensual AS
SELECT
    t.year,
    t.month,
    t.month_name,
    dr.restaurant_name,
    dr.geographic_zone,
    COALESCE(o.ordenes_mes, 0) AS ordenes_mes,
    COALESCE(r.reservaciones_mes, 0) AS reservaciones_mes,
    COALESCE(o.ingresos_mes, 0) AS ingresos_mes,
    COALESCE(o.clientes_nuevos_mes, 0) AS clientes_nuevos_mes,
    COALESCE(o.ticket_promedio, 0) AS ticket_promedio
FROM dim_restaurant dr
CROSS JOIN (
    SELECT DISTINCT year, month, month_name
    FROM dim_time
) t
LEFT JOIN (
    SELECT
        fo.restaurant_id,
        dt.year,
        dt.month,
        COUNT(DISTINCT fo.order_id) AS ordenes_mes,
        SUM(fo.final_amount) AS ingresos_mes,
        COUNT(DISTINCT fo.customer_id) AS clientes_nuevos_mes,
        AVG(fo.final_amount) AS ticket_promedio
    FROM fact_orders fo
    INNER JOIN dim_time dt ON fo.time_id = dt.time_id
    GROUP BY fo.restaurant_id, dt.year, dt.month
) o ON dr.restaurant_id = o.restaurant_id
    AND t.year = o.year
    AND t.month = o.month
LEFT JOIN (
    SELECT
        fr.restaurant_id,
        dt.year,
        dt.month,
        COUNT(DISTINCT fr.reservation_id) AS reservaciones_mes
    FROM fact_reservations fr
    INNER JOIN dim_time dt ON fr.time_id = dt.time_id
    GROUP BY fr.restaurant_id, dt.year, dt.month
) r ON dr.restaurant_id = r.restaurant_id
    AND t.year = r.year
    AND t.month = r.month;

-- =====================================================
-- CUBO 6: CLIENTES - LEALTAD Y COMPORTAMIENTO
-- =====================================================
DROP VIEW IF EXISTS cubo_lealtad_clientes;

CREATE VIEW cubo_lealtad_clientes AS
SELECT
    dc.customer_id,
    dc.customer_name,
    dc.customer_type,
    dc.geographic_zone,
    dc.loyalty_level,
    COALESCE(o.total_ordenes_cliente, 0) AS total_ordenes_cliente,
    COALESCE(r.total_reservaciones_cliente, 0) AS total_reservaciones_cliente,
    COALESCE(o.gasto_total_cliente, 0) AS gasto_total_cliente,
    COALESCE(o.ticket_promedio_cliente, 0) AS ticket_promedio_cliente,
    o.primera_compra,
    o.ultima_compra,
    COALESCE(o.dias_desde_primera_compra, 0) AS dias_desde_primera_compra
FROM dim_customer dc
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_ordenes_cliente,
        SUM(final_amount) AS gasto_total_cliente,
        AVG(final_amount) AS ticket_promedio_cliente,
        MIN(order_time) AS primera_compra,
        MAX(order_time) AS ultima_compra,
        DATEDIFF(CAST(MAX(order_time) AS DATE), CAST(MIN(order_time) AS DATE)) AS dias_desde_primera_compra
    FROM fact_orders
    GROUP BY customer_id
) o ON dc.customer_id = o.customer_id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(DISTINCT reservation_id) AS total_reservaciones_cliente
    FROM fact_reservations
    GROUP BY customer_id
) r ON dc.customer_id = r.customer_id;

-- =====================================================
-- CUBO 7: PRODUCTOS - BESTSELLERS
-- =====================================================
DROP VIEW IF EXISTS cubo_bestsellers_productos;

CREATE VIEW cubo_bestsellers_productos AS
SELECT
    product_id,
    product_name,
    category,
    subcategory,
    price,
    margin,
    veces_vendido,
    cantidad_total,
    ingresos_producto,
    precio_promedio_venta,
    costo_total,
    ganancia_total,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY ingresos_producto DESC) AS ranking_categoria
FROM (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.price,
        p.margin,
        COUNT(fo.order_id) AS veces_vendido,
        COALESCE(SUM(fo.quantity), 0) AS cantidad_total,
        COALESCE(SUM(fo.final_amount), 0) AS ingresos_producto,
        COALESCE(AVG(fo.final_amount), 0) AS precio_promedio_venta,
        COALESCE(SUM(fo.quantity * p.cost), 0) AS costo_total,
        COALESCE(SUM(fo.final_amount - (fo.quantity * p.cost)), 0) AS ganancia_total
    FROM dim_product p
    LEFT JOIN fact_orders fo ON p.product_id = fo.product_id
    GROUP BY
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.price,
        p.margin
) productos;

-- =====================================================
-- CUBO 8: RENDIMIENTO POR RESTAURANTE
-- =====================================================
DROP VIEW IF EXISTS cubo_rendimiento_restaurantes;

CREATE VIEW cubo_rendimiento_restaurantes AS
SELECT
    dr.restaurant_id,
    dr.restaurant_name,
    dr.location,
    dr.geographic_zone,
    dr.capacity,
    COALESCE(o.total_ordenes, 0) AS total_ordenes,
    COALESCE(r.total_reservaciones, 0) AS total_reservaciones,
    COALESCE(o.ingresos_totales, 0) AS ingresos_totales,
    COALESCE(o.ticket_promedio, 0) AS ticket_promedio,
    COALESCE(o.clientes_unicos, 0) AS clientes_unicos,
    COALESCE(r.personas_atendidas, 0) AS personas_atendidas,
    COALESCE(r.duracion_promedio_reserva, 0) AS duracion_promedio_reserva,
    COALESCE(r.no_shows, 0) AS no_shows,
    CASE
        WHEN COALESCE(r.total_reservaciones, 0) > 0
        THEN (COALESCE(r.no_shows, 0) * 100.0 / r.total_reservaciones)
        ELSE 0
    END AS porcentaje_no_show
FROM dim_restaurant dr
LEFT JOIN (
    SELECT
        restaurant_id,
        COUNT(DISTINCT order_id) AS total_ordenes,
        SUM(final_amount) AS ingresos_totales,
        AVG(final_amount) AS ticket_promedio,
        COUNT(DISTINCT customer_id) AS clientes_unicos
    FROM fact_orders
    GROUP BY restaurant_id
) o ON dr.restaurant_id = o.restaurant_id
LEFT JOIN (
    SELECT
        restaurant_id,
        COUNT(DISTINCT reservation_id) AS total_reservaciones,
        SUM(party_size) AS personas_atendidas,
        AVG(duration_minutes) AS duracion_promedio_reserva,
        SUM(CASE WHEN no_show = true THEN 1 ELSE 0 END) AS no_shows
    FROM fact_reservations
    GROUP BY restaurant_id
) r ON dr.restaurant_id = r.restaurant_id;

-- =====================================================
-- CUBO 9: OCUPACION Y UTILIZACION DE MESAS
-- =====================================================
DROP VIEW IF EXISTS cubo_ocupacion_mesas;

CREATE VIEW cubo_ocupacion_mesas AS
SELECT
    dr.restaurant_id,
    dr.restaurant_name,
    t.month_name,
    t.day_name,
    COUNT(DISTINCT fr.reservation_id) AS reservaciones_realizadas,
    SUM(CASE WHEN fr.table_occupied = true THEN 1 ELSE 0 END) AS mesas_ocupadas,
    CASE
        WHEN dr.capacity > 0
        THEN (COUNT(DISTINCT fr.reservation_id) * 100.0 / dr.capacity)
        ELSE 0
    END AS porcentaje_ocupacion,
    COALESCE(AVG(fr.party_size), 0) AS tamano_promedio_grupo,
    CASE
        WHEN COUNT(fr.reservation_id) > 0
        THEN (SUM(fr.duration_minutes) / COUNT(fr.reservation_id))
        ELSE 0
    END AS minutos_promedio_ocupacion
FROM fact_reservations fr
INNER JOIN dim_restaurant dr ON fr.restaurant_id = dr.restaurant_id
INNER JOIN dim_time t ON fr.time_id = t.time_id
GROUP BY
    dr.restaurant_id,
    dr.restaurant_name,
    t.month_name,
    t.day_name,
    dr.capacity;

-- =====================================================
-- CUBO 10: ANALISIS DE RENTABILIDAD
-- =====================================================
DROP VIEW IF EXISTS cubo_rentabilidad;

CREATE VIEW cubo_rentabilidad AS
SELECT
    dr.restaurant_id,
    dr.restaurant_name,
    t.year,
    t.month,
    t.month_name,
    SUM(fo.final_amount) AS ingresos_brutos,
    SUM(COALESCE(fo.quantity * p.cost, 0)) AS costo_productos,
    SUM(COALESCE(fo.final_amount - (fo.quantity * p.cost), 0)) AS ganancia_bruta,
    CASE
        WHEN SUM(fo.final_amount) > 0
        THEN ROUND((SUM(COALESCE(fo.final_amount - (fo.quantity * p.cost), 0)) / SUM(fo.final_amount) * 100), 2)
        ELSE 0
    END AS margen_porcentaje,
    COUNT(fo.order_id) AS total_ordenes,
    AVG(fo.final_amount) AS ticket_promedio,
    COUNT(DISTINCT fo.customer_id) AS clientes_unicos
FROM fact_orders fo
INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
GROUP BY
    dr.restaurant_id,
    dr.restaurant_name,
    t.year,
    t.month,
    t.month_name;
