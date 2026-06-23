-- =====================================================
-- Seed de datos para prueba completa del Data Warehouse
-- Ejecutar despues de crear schema_star.sql
-- =====================================================

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/dim_time.csv'
OVERWRITE INTO TABLE dim_time;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/dim_customer.csv'
OVERWRITE INTO TABLE dim_customer;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/dim_product.csv'
OVERWRITE INTO TABLE dim_product;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/dim_restaurant.csv'
OVERWRITE INTO TABLE dim_restaurant;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/dim_status.csv'
OVERWRITE INTO TABLE dim_status;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/fact_orders.csv'
OVERWRITE INTO TABLE fact_orders;

LOAD DATA LOCAL INPATH '/workspace/warehouse/seed/fact_reservations.csv'
OVERWRITE INTO TABLE fact_reservations;
