-- =====================================================
-- VISTAS OLAP - CUBOS DE ANÁLISIS
-- Base de Datos II - Proyecto OLAP
-- =====================================================

-- =====================================================
-- CUBO 1: INGRESOS POR MES Y CATEGORÍA DE PRODUCTO
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_ingresos_mes_categoria AS
SELECT 
    t.year,
    t.month,
    t.month_name,
    p.category,
    COUNT(DISTINCT fo.order_id) as total_ordenes,
    SUM(fo.quantity) as total_cantidad_items,
    SUM(fo.final_amount) as ingresos_totales,
    AVG(fo.final_amount) as promedio_orden,
    SUM(fo.net_amount) as ingresos_netos,
    SUM(fo.tax_amount) as impuestos_totales,
    SUM(fo.discount) as descuentos_totales
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
GROUP BY t.year, t.month, t.month_name, p.category;

-- =====================================================
-- CUBO 2: ACTIVIDAD DE CLIENTES POR ZONA GEOGRÁFICA
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_actividad_clientes_zona AS
SELECT 
    dc.geographic_zone,
    dr.location as restaurant_location,
    COUNT(DISTINCT dc.customer_id) as total_clientes_unicos,
    COUNT(DISTINCT fo.order_id) as total_ordenes,
    COUNT(DISTINCT fr.reservation_id) as total_reservaciones,
    SUM(fo.final_amount) as ingresos_zona,
    AVG(fo.final_amount) as ticket_promedio,
    AVG(fr.party_size) as tamaño_promedio_grupo,
    SUM(CASE WHEN fr.no_show = true THEN 1 ELSE 0 END) as reservaciones_no_show
FROM fact_orders fo
FULL OUTER JOIN fact_reservations fr ON fo.customer_id = fr.customer_id
INNER JOIN dim_customer dc ON fo.customer_id = dc.customer_id OR fr.customer_id = dc.customer_id
INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id OR fr.restaurant_id = dr.restaurant_id
GROUP BY dc.geographic_zone, dr.location;

-- =====================================================
-- CUBO 3: ESTADÍSTICAS ÓRDENES COMPLETADAS VS CANCELADAS
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_ordenes_completadas_canceladas AS
SELECT 
    t.year,
    t.month,
    t.month_name,
    t.quarter,
    ds.status_name,
    COUNT(fo.order_id) as cantidad_ordenes,
    SUM(fo.final_amount) as monto_total,
    AVG(fo.final_amount) as ticket_promedio,
    COUNT(DISTINCT fo.customer_id) as clientes_unicos,
    COUNT(DISTINCT fo.restaurant_id) as restaurantes_involucrados,
    (COUNT(fo.order_id) * 100.0 / SUM(COUNT(fo.order_id)) OVER (PARTITION BY t.year, t.month)) as porcentaje_estado
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_status ds ON fo.status_id = ds.status_id
WHERE ds.status_type = 'order'
GROUP BY t.year, t.month, t.month_name, t.quarter, ds.status_name;

-- =====================================================
-- CUBO 4: TENDENCIAS DE CONSUMO - HORARIOS PICO
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_tendencias_horarios_pico AS
SELECT 
    t.day_name,
    t.month_name,
    HOUR(fo.order_time) as hora,
    p.category,
    COUNT(fo.order_id) as ordenes_por_hora,
    SUM(fo.quantity) as items_vendidos,
    SUM(fo.final_amount) as ingresos_hora,
    AVG(fo.final_amount) as ticket_promedio,
    COUNT(DISTINCT fo.customer_id) as clientes_unicos
FROM fact_orders fo
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
GROUP BY t.day_name, t.month_name, HOUR(fo.order_time), p.category
ORDER BY ordenes_por_hora DESC;

-- =====================================================
-- CUBO 5: CRECIMIENTO MENSUAL Y ANÁLISIS COMPARATIVO
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_crecimiento_mensual AS
SELECT 
    t.year,
    t.month,
    t.month_name,
    dr.restaurant_name,
    dr.geographic_zone,
    COUNT(fo.order_id) as ordenes_mes,
    COUNT(fr.reservation_id) as reservaciones_mes,
    SUM(fo.final_amount) as ingresos_mes,
    COUNT(DISTINCT fo.customer_id) as clientes_nuevos_mes,
    AVG(fo.final_amount) as ticket_promedio,
    -- Cálculo de crecimiento mes anterior
    LAG(COUNT(fo.order_id)) OVER (PARTITION BY dr.restaurant_id ORDER BY t.year, t.month) as ordenes_mes_anterior,
    LAG(SUM(fo.final_amount)) OVER (PARTITION BY dr.restaurant_id ORDER BY t.year, t.month) as ingresos_mes_anterior,
    ROUND(((SUM(fo.final_amount) - LAG(SUM(fo.final_amount)) OVER (PARTITION BY dr.restaurant_id ORDER BY t.year, t.month)) / 
           LAG(SUM(fo.final_amount)) OVER (PARTITION BY dr.restaurant_id ORDER BY t.year, t.month) * 100), 2) as porcentaje_crecimiento
FROM fact_orders fo
FULL OUTER JOIN fact_reservations fr ON fo.time_id = fr.time_id
INNER JOIN dim_time t ON fo.time_id = t.time_id OR fr.time_id = t.time_id
INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id OR fr.restaurant_id = dr.restaurant_id
GROUP BY t.year, t.month, t.month_name, dr.restaurant_name, dr.geographic_zone;

-- =====================================================
-- CUBO 6: ANÁLISIS DE CLIENTES - LEALTAD Y COMPORTAMIENTO
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_lealtad_clientes AS
SELECT 
    dc.customer_id,
    dc.customer_name,
    dc.customer_type,
    dc.geographic_zone,
    dc.loyalty_level,
    COUNT(DISTINCT fo.order_id) as total_ordenes_cliente,
    COUNT(DISTINCT fr.reservation_id) as total_reservaciones_cliente,
    SUM(fo.final_amount) as gasto_total_cliente,
    AVG(fo.final_amount) as ticket_promedio_cliente,
    MIN(fo.order_time) as primera_compra,
    MAX(fo.order_time) as ultima_compra,
    DATEDIFF(MAX(fo.order_time), MIN(fo.order_time)) as dias_desde_primera_compra,
    (COUNT(DISTINCT fo.order_id) / (DATEDIFF(MAX(fo.order_time), MIN(fo.order_time)) + 1)) as frecuencia_compra_diaria
FROM dim_customer dc
LEFT JOIN fact_orders fo ON dc.customer_id = fo.customer_id
LEFT JOIN fact_reservations fr ON dc.customer_id = fr.customer_id
GROUP BY dc.customer_id, dc.customer_name, dc.customer_type, dc.geographic_zone, dc.loyalty_level;

-- =====================================================
-- CUBO 7: ANÁLISIS DE PRODUCTOS - BESTSELLERS
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_bestsellers_productos AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.price,
    p.margin,
    COUNT(fo.order_id) as veces_vendido,
    SUM(fo.quantity) as cantidad_total,
    SUM(fo.final_amount) as ingresos_producto,
    AVG(fo.final_amount) as precio_promedio_venta,
    SUM(fo.quantity * p.cost) as costo_total,
    SUM(fo.final_amount - (fo.quantity * p.cost)) as ganancia_total,
    RANK() OVER (PARTITION BY p.category ORDER BY SUM(fo.final_amount) DESC) as ranking_categoria
FROM dim_product p
LEFT JOIN fact_orders fo ON p.product_id = fo.product_id
GROUP BY p.product_id, p.product_name, p.category, p.subcategory, p.price, p.margin;

-- =====================================================
-- CUBO 8: RENDIMIENTO POR RESTAURANTE
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_rendimiento_restaurantes AS
SELECT 
    dr.restaurant_id,
    dr.restaurant_name,
    dr.location,
    dr.geographic_zone,
    dr.capacity,
    COUNT(DISTINCT fo.order_id) as total_ordenes,
    COUNT(DISTINCT fr.reservation_id) as total_reservaciones,
    SUM(fo.final_amount) as ingresos_totales,
    AVG(fo.final_amount) as ticket_promedio,
    COUNT(DISTINCT fo.customer_id) as clientes_unicos,
    SUM(fr.party_size) as personas_atendidas,
    AVG(fr.duration_minutes) as duracion_promedio_reserva,
    SUM(CASE WHEN fr.no_show = true THEN 1 ELSE 0 END) as no_shows,
    (SUM(CASE WHEN fr.no_show = true THEN 1 ELSE 0 END) * 100.0 / COUNT(fr.reservation_id)) as porcentaje_no_show
FROM dim_restaurant dr
LEFT JOIN fact_orders fo ON dr.restaurant_id = fo.restaurant_id
LEFT JOIN fact_reservations fr ON dr.restaurant_id = fr.restaurant_id
GROUP BY dr.restaurant_id, dr.restaurant_name, dr.location, dr.geographic_zone, dr.capacity;

-- =====================================================
-- CUBO 9: OCUPACIÓN Y UTILIZACIÓN DE MESAS
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_ocupacion_mesas AS
SELECT 
    dr.restaurant_id,
    dr.restaurant_name,
    t.month_name,
    t.day_name,
    COUNT(DISTINCT fr.reservation_id) as reservaciones_realizadas,
    SUM(CASE WHEN fr.table_occupied = true THEN 1 ELSE 0 END) as mesas_ocupadas,
    COUNT(DISTINCT fr.reservation_id) * 100.0 / dr.capacity as porcentaje_ocupacion,
    AVG(fr.party_size) as tamaño_promedio_grupo,
    SUM(fr.duration_minutes) / COUNT(fr.reservation_id) as minutos_promedio_ocupacion
FROM fact_reservations fr
INNER JOIN dim_restaurant dr ON fr.restaurant_id = dr.restaurant_id
INNER JOIN dim_time t ON fr.time_id = t.time_id
GROUP BY dr.restaurant_id, dr.restaurant_name, t.month_name, t.day_name;

-- =====================================================
-- CUBO 10: ANÁLISIS DE RENTABILIDAD
-- =====================================================
CREATE VIEW IF NOT EXISTS cubo_rentabilidad AS
SELECT 
    dr.restaurant_id,
    dr.restaurant_name,
    t.year,
    t.month,
    t.month_name,
    SUM(fo.final_amount) as ingresos_brutos,
    SUM(fo.quantity * p.cost) as costo_productos,
    SUM(fo.final_amount - (fo.quantity * p.cost)) as ganancia_bruta,
    ROUND((SUM(fo.final_amount - (fo.quantity * p.cost)) / SUM(fo.final_amount) * 100), 2) as margen_porcentaje,
    COUNT(fo.order_id) as total_ordenes,
    AVG(fo.final_amount) as ticket_promedio,
    COUNT(DISTINCT fo.customer_id) as clientes_unicos
FROM fact_orders fo
INNER JOIN dim_restaurant dr ON fo.restaurant_id = dr.restaurant_id
INNER JOIN dim_time t ON fo.time_id = t.time_id
INNER JOIN dim_product p ON fo.product_id = p.product_id
GROUP BY dr.restaurant_id, dr.restaurant_name, t.year, t.month, t.month_name;
