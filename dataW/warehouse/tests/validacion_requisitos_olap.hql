-- =====================================================
-- =====================================================
-- =====================================================

--para correr estas preubas del DW ejecute este comando desde la raiz:
-- .\dataW\warehouse\tests\run_full_dw_validation.ps1

-- =====================================================
-- =====================================================
-- =====================================================

-- =====================================================
-- Validacion de requisitos OLAP y Data Warehouse
-- Ejecutar despues de schemas/schema_star.sql y schemas/hive_olap_views.sql
-- Comando sugerido:
-- hive -f dataW/warehouse/tests/validacion_requisitos_olap.hql
-- =====================================================

-- 1. Evidencia de esquema estrella:
-- Deben aparecer dimensiones dim_* y hechos fact_*.
SHOW TABLES;

DESCRIBE dim_time;
DESCRIBE dim_customer;
DESCRIBE dim_product;
DESCRIBE dim_restaurant;
DESCRIBE dim_status;
DESCRIBE fact_orders;
DESCRIBE fact_reservations;

-- 2. Evidencia de datos historicos cargados:
-- Para cumplir de verdad, estas tablas no deberian estar en 0.
SELECT 'dim_time' AS tabla, COUNT(*) AS total_registros FROM dim_time
UNION ALL
SELECT 'dim_customer' AS tabla, COUNT(*) AS total_registros FROM dim_customer
UNION ALL
SELECT 'dim_product' AS tabla, COUNT(*) AS total_registros FROM dim_product
UNION ALL
SELECT 'dim_restaurant' AS tabla, COUNT(*) AS total_registros FROM dim_restaurant
UNION ALL
SELECT 'dim_status' AS tabla, COUNT(*) AS total_registros FROM dim_status
UNION ALL
SELECT 'fact_orders' AS tabla, COUNT(*) AS total_registros FROM fact_orders
UNION ALL
SELECT 'fact_reservations' AS tabla, COUNT(*) AS total_registros FROM fact_reservations;

-- 2.1. Evidencia de historico:
-- Debe cubrir mas de un periodo si el requisito pide datos historicos.
SELECT
    MIN(full_date) AS fecha_minima,
    MAX(full_date) AS fecha_maxima,
    COUNT(DISTINCT year) AS anios_cubiertos,
    COUNT(DISTINCT month) AS meses_cubiertos
FROM dim_time;

SELECT
    MIN(CAST(order_time AS DATE)) AS primera_orden,
    MAX(CAST(order_time AS DATE)) AS ultima_orden
FROM fact_orders
WHERE order_time IS NOT NULL;

SELECT
    MIN(reservation_date) AS primera_reserva,
    MAX(reservation_date) AS ultima_reserva
FROM fact_reservations
WHERE reservation_date IS NOT NULL;

-- 3. Evidencia de vistas/cubos OLAP:
-- El requisito pide al menos 5; este proyecto define 10.
SHOW VIEWS;

-- 4. Cubo por tiempo y tipo de producto:
SELECT
    year,
    month,
    month_name,
    category,
    total_ordenes,
    ingresos_totales
FROM cubo_ingresos_mes_categoria
ORDER BY year DESC, month DESC, ingresos_totales DESC
LIMIT 20;

-- 5. Cubo por ubicacion:
SELECT
    geographic_zone,
    restaurant_location,
    total_clientes_unicos,
    total_ordenes,
    total_reservaciones,
    ingresos_zona
FROM cubo_actividad_clientes_zona
ORDER BY ingresos_zona DESC
LIMIT 20;

-- 6. Cubo por frecuencia de uso / horarios:
SELECT
    day_name,
    month_name,
    hora,
    category,
    ordenes_por_hora,
    items_vendidos
FROM cubo_tendencias_horarios_pico
ORDER BY ordenes_por_hora DESC
LIMIT 20;

-- 7. Cubo de frecuencia por cliente:
SELECT
    customer_id,
    customer_name,
    customer_type,
    loyalty_level,
    total_ordenes_cliente,
    total_reservaciones_cliente,
    gasto_total_cliente
FROM cubo_lealtad_clientes
ORDER BY total_ordenes_cliente DESC, total_reservaciones_cliente DESC
LIMIT 20;

-- 8. Cubo de productos:
SELECT
    product_name,
    category,
    veces_vendido,
    cantidad_total,
    ingresos_producto,
    ranking_categoria
FROM cubo_bestsellers_productos
WHERE ranking_categoria <= 5
ORDER BY category, ranking_categoria;

-- 9. Cubo de rendimiento por restaurante:
SELECT
    restaurant_name,
    location,
    geographic_zone,
    total_ordenes,
    total_reservaciones,
    ingresos_totales,
    porcentaje_no_show
FROM cubo_rendimiento_restaurantes
ORDER BY ingresos_totales DESC
LIMIT 20;

-- 10. Cubo de ocupacion de mesas:
SELECT
    restaurant_name,
    month_name,
    day_name,
    reservaciones_realizadas,
    mesas_ocupadas,
    porcentaje_ocupacion,
    tamano_promedio_grupo
FROM cubo_ocupacion_mesas
ORDER BY porcentaje_ocupacion DESC
LIMIT 20;


