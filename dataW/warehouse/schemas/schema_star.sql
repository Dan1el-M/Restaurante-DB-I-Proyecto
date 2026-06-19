-- =====================================================
-- DATA WAREHOUSE - ESQUEMA ESTRELLA PARA HIVE
-- Base de Datos II - Proyecto OLAP
-- =====================================================
--
-- Nota:
-- Hive no aplica claves primarias ni foraneas como una base relacional.
-- Las relaciones del esquema estrella se mantienen por convencion de columnas:
-- dim_* son dimensiones y fact_* son tablas de hechos.

-- =====================================================
-- 1. DIMENSION: TIEMPO
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INT,
    full_date DATE,
    day_of_week INT,
    day_name STRING,
    week_of_year INT,
    month INT,
    month_name STRING,
    quarter INT,
    year INT,
    is_weekend BOOLEAN,
    season STRING
)
STORED AS TEXTFILE;

-- =====================================================
-- 2. DIMENSION: CLIENTE
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id INT,
    customer_name STRING,
    customer_type STRING,
    registration_date DATE,
    preferred_restaurant_id INT,
    geographic_zone STRING,
    loyalty_level INT,
    total_spent DOUBLE,
    total_orders INT,
    is_active BOOLEAN
)
STORED AS TEXTFILE;

-- =====================================================
-- 3. DIMENSION: PRODUCTO / MENU
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_product (
    product_id INT,
    product_name STRING,
    category STRING,
    subcategory STRING,
    price DOUBLE,
    cost DOUBLE,
    margin DOUBLE,
    is_available BOOLEAN,
    creation_date DATE,
    last_update DATE
)
STORED AS TEXTFILE;

-- =====================================================
-- 4. DIMENSION: RESTAURANTE
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_restaurant (
    restaurant_id INT,
    restaurant_name STRING,
    location STRING,
    geographic_zone STRING,
    capacity INT,
    opening_year INT,
    phone STRING,
    email STRING,
    status STRING
)
STORED AS TEXTFILE;

-- =====================================================
-- 5. DIMENSION: ESTADO
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_status (
    status_id INT,
    status_name STRING,
    status_type STRING,
    description STRING
)
STORED AS TEXTFILE;

-- =====================================================
-- 6. HECHOS: ORDENES
-- =====================================================
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id INT,
    customer_id INT,
    restaurant_id INT,
    product_id INT,
    time_id INT,
    status_id INT,
    quantity INT,
    unit_price DOUBLE,
    total_amount DOUBLE,
    discount DOUBLE,
    net_amount DOUBLE,
    tax_amount DOUBLE,
    final_amount DOUBLE,
    order_time TIMESTAMP,
    delivery_time TIMESTAMP
)
STORED AS TEXTFILE;

-- =====================================================
-- 7. HECHOS: RESERVACIONES
-- =====================================================
CREATE TABLE IF NOT EXISTS fact_reservations (
    reservation_id INT,
    customer_id INT,
    restaurant_id INT,
    time_id INT,
    status_id INT,
    party_size INT,
    duration_minutes INT,
    table_occupied BOOLEAN,
    no_show BOOLEAN,
    reservation_date DATE,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP
)
STORED AS TEXTFILE;
