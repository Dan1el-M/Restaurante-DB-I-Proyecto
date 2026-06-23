-- Generated from operational API /graph/export. Do not edit manually.
TRUNCATE TABLE fact_orders;
TRUNCATE TABLE fact_reservations;
TRUNCATE TABLE dim_status;
TRUNCATE TABLE dim_customer;
TRUNCATE TABLE dim_product;
TRUNCATE TABLE dim_restaurant;
TRUNCATE TABLE dim_time;

INSERT INTO dim_time VALUES
(20260101, CAST('2026-01-01' AS DATE), 4, 'Thursday', 0, 1, 'January', 1, 2026, false, 'N/A');

INSERT INTO dim_customer VALUES
(1, 'admin', 'admin', CAST('2026-01-01' AS DATE), 1, 'Central', 1, 300.0, 1, true);

INSERT INTO dim_product VALUES
(1, 'Huevo', 'Desayuno', 'Desayuno', 300.0, 180.0, 120.0, true, CAST('2026-01-01' AS DATE), CAST('2026-01-01' AS DATE));

INSERT INTO dim_restaurant VALUES
(1, 'Rompoi', 'Central', 'Central', 60, 2020, '2222-0001', 'restaurante1@local', 'Activo');

INSERT INTO dim_status VALUES
(1, 'Completed', 'order', 'Orden completada'),
(2, 'Cancelled', 'order', 'Orden cancelada'),
(3, 'Pending', 'order', 'Orden pendiente'),
(4, 'Confirmed', 'reservation', 'Reserva confirmada'),
(5, 'No Show', 'reservation', 'Cliente no asistio'),
(6, 'Cancelled', 'reservation', 'Reserva cancelada');

INSERT INTO fact_orders VALUES
(1, 1, 1, 1, 20260101, 1, 1, 300.0, 300.0, 0.0, 300.0, 39.0, 339.0, CAST('2026-01-01 13:00:00' AS TIMESTAMP), CAST('2026-01-01 13:35:00' AS TIMESTAMP));

-- No reservation source table is required for the three Superset dashboards.