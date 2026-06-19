-- =====================================================
-- DATA WAREHOUSE - ESQUEMA ESTRELLA (STAR SCHEMA)
-- Base de Datos II - Proyecto OLAP
-- =====================================================

-- =====================================================
-- 1. TABLA DE DIMENSIÓN: TIEMPO (dim_time)
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INT NOT NULL PRIMARY KEY,
    full_date DATE NOT NULL,
    day_of_week INT,
    day_name STRING,
    week_of_year INT,
    month INT,
    month_name STRING,
    quarter INT,
    year INT,
    is_weekend BOOLEAN,
    season STRING
);

-- =====================================================
-- 2. TABLA DE DIMENSIÓN: CLIENTE (dim_customer)
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id INT NOT NULL PRIMARY KEY,
    customer_name STRING NOT NULL,
    customer_type STRING,  -- Regular, VIP, etc.
    registration_date DATE,
    preferred_restaurant_id INT,
    geographic_zone STRING,  -- Zona geográfica (norte, sur, centro, etc.)
    loyalty_level INT,  -- Nivel de lealtad
    total_spent DOUBLE,  -- Monto total gastado
    total_orders INT,  -- Total de órdenes
    is_active BOOLEAN
);

-- =====================================================
-- 3. TABLA DE DIMENSIÓN: PRODUCTO/MENÚ (dim_product)
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_product (
    product_id INT NOT NULL PRIMARY KEY,
    product_name STRING NOT NULL,
    category STRING NOT NULL,  -- Entrada, Plato principal, Postre, Bebida, etc.
    subcategory STRING,
    price DOUBLE NOT NULL,
    cost DOUBLE,  -- Costo del producto
    margin DOUBLE,  -- Margen de ganancia
    is_available BOOLEAN,
    creation_date DATE,
    last_update DATE
);

-- =====================================================
-- 4. TABLA DE DIMENSIÓN: RESTAURANTE (dim_restaurant)
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_restaurant (
    restaurant_id INT NOT NULL PRIMARY KEY,
    restaurant_name STRING NOT NULL,
    location STRING NOT NULL,
    geographic_zone STRING,  -- Zona geográfica
    capacity INT,  -- Capacidad total de mesas
    opening_year INT,
    phone STRING,
    email STRING,
    status STRING  -- Activo, Inactivo, etc.
);

-- =====================================================
-- 5. TABLA DE DIMENSIÓN: ESTADO (dim_status)
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_status (
    status_id INT NOT NULL PRIMARY KEY,
    status_name STRING NOT NULL,
    status_type STRING,  -- 'order' o 'reservation'
    description STRING
);

-- =====================================================
-- 6. TABLA DE HECHOS: ÓRDENES (fact_orders)
-- =====================================================
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id INT NOT NULL PRIMARY KEY,
    customer_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    product_id INT NOT NULL,
    time_id INT NOT NULL,
    status_id INT NOT NULL,
    
    -- Métricas cuantificables
    quantity INT NOT NULL,
    unit_price DOUBLE NOT NULL,
    total_amount DOUBLE NOT NULL,
    discount DOUBLE DEFAULT 0,
    net_amount DOUBLE NOT NULL,
    tax_amount DOUBLE NOT NULL,
    final_amount DOUBLE NOT NULL,
    
    -- Dimensiones de tiempo adicionales
    order_time TIMESTAMP,
    delivery_time TIMESTAMP,
    
    -- Claves foráneas
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    CONSTRAINT fk_orders_restaurant FOREIGN KEY (restaurant_id) REFERENCES dim_restaurant(restaurant_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
    CONSTRAINT fk_orders_time FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    CONSTRAINT fk_orders_status FOREIGN KEY (status_id) REFERENCES dim_status(status_id)
);

-- =====================================================
-- 7. TABLA DE HECHOS: RESERVACIONES (fact_reservations)
-- =====================================================
CREATE TABLE IF NOT EXISTS fact_reservations (
    reservation_id INT NOT NULL PRIMARY KEY,
    customer_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    time_id INT NOT NULL,
    status_id INT NOT NULL,
    
    -- Métricas
    party_size INT NOT NULL,  -- Número de personas
    duration_minutes INT,  -- Duración de la reserva
    table_occupied BOOLEAN,
    no_show BOOLEAN DEFAULT FALSE,
    
    -- Tiempos
    reservation_date DATE,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    
    -- Claves foráneas
    CONSTRAINT fk_reservations_customer FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    CONSTRAINT fk_reservations_restaurant FOREIGN KEY (restaurant_id) REFERENCES dim_restaurant(restaurant_id),
    CONSTRAINT fk_reservations_time FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    CONSTRAINT fk_reservations_status FOREIGN KEY (status_id) REFERENCES dim_status(status_id)
);

-- =====================================================
-- Índices para optimizar consultas
-- =====================================================
CREATE INDEX idx_fact_orders_time ON fact_orders(time_id);
CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_fact_orders_restaurant ON fact_orders(restaurant_id);
CREATE INDEX idx_fact_orders_status ON fact_orders(status_id);

CREATE INDEX idx_fact_reservations_time ON fact_reservations(time_id);
CREATE INDEX idx_fact_reservations_customer ON fact_reservations(customer_id);
CREATE INDEX idx_fact_reservations_restaurant ON fact_reservations(restaurant_id);
