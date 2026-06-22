-- =====================================================
-- Seed de datos para prueba completa del Data Warehouse
-- Ejecutar despues de crear schema_star.sql
-- =====================================================

TRUNCATE TABLE fact_orders;
TRUNCATE TABLE fact_reservations;
TRUNCATE TABLE dim_status;
TRUNCATE TABLE dim_customer;
TRUNCATE TABLE dim_product;
TRUNCATE TABLE dim_restaurant;
TRUNCATE TABLE dim_time;

INSERT INTO dim_time VALUES
(20240105, CAST('2024-01-05' AS DATE), 5, 'Friday', 1, 1, 'January', 1, 2024, false, 'Summer'),
(20240106, CAST('2024-01-06' AS DATE), 6, 'Saturday', 1, 1, 'January', 1, 2024, true, 'Summer'),
(20240210, CAST('2024-02-10' AS DATE), 6, 'Saturday', 6, 2, 'February', 1, 2024, true, 'Summer'),
(20240214, CAST('2024-02-14' AS DATE), 3, 'Wednesday', 7, 2, 'February', 1, 2024, false, 'Summer'),
(20240303, CAST('2024-03-03' AS DATE), 7, 'Sunday', 9, 3, 'March', 1, 2024, true, 'Summer'),
(20240315, CAST('2024-03-15' AS DATE), 5, 'Friday', 11, 3, 'March', 1, 2024, false, 'Summer');

INSERT INTO dim_customer VALUES
(1, 'Ana Mora', 'VIP', CAST('2023-05-10' AS DATE), 1, 'Central', 5, 86000.0, 8, true),
(2, 'Carlos Rojas', 'Regular', CAST('2023-08-22' AS DATE), 2, 'Oeste', 2, 24500.0, 3, true),
(3, 'Maria Solis', 'Regular', CAST('2024-01-03' AS DATE), 1, 'Central', 3, 43000.0, 5, true),
(4, 'Jose Vega', 'Nuevo', CAST('2024-02-11' AS DATE), 3, 'Este', 1, 12000.0, 1, true);

INSERT INTO dim_product VALUES
(1, 'Hamburguesa Clasica', 'Plato fuerte', 'Hamburguesas', 6500.0, 3200.0, 3300.0, true, CAST('2023-01-01' AS DATE), CAST('2024-01-01' AS DATE)),
(2, 'Pizza Margarita', 'Plato fuerte', 'Pizzas', 7200.0, 3600.0, 3600.0, true, CAST('2023-01-01' AS DATE), CAST('2024-01-01' AS DATE)),
(3, 'Ensalada Verde', 'Entrada', 'Ensaladas', 4200.0, 1800.0, 2400.0, true, CAST('2023-01-01' AS DATE), CAST('2024-01-01' AS DATE)),
(4, 'Cheesecake', 'Postre', 'Dulces', 3800.0, 1500.0, 2300.0, true, CAST('2023-01-01' AS DATE), CAST('2024-01-01' AS DATE)),
(5, 'Cafe Frio', 'Bebida', 'Cafe', 2500.0, 900.0, 1600.0, true, CAST('2023-01-01' AS DATE), CAST('2024-01-01' AS DATE));

INSERT INTO dim_restaurant VALUES
(1, 'Restaurante Central', 'San Jose', 'Central', 80, 2020, '2222-1000', 'central@test.com', 'Activo'),
(2, 'Restaurante Oeste', 'Escazu', 'Oeste', 60, 2021, '2222-2000', 'oeste@test.com', 'Activo'),
(3, 'Restaurante Este', 'Cartago', 'Este', 45, 2022, '2222-3000', 'este@test.com', 'Activo');

INSERT INTO dim_status VALUES
(1, 'Completed', 'order', 'Orden completada'),
(2, 'Cancelled', 'order', 'Orden cancelada'),
(3, 'Pending', 'order', 'Orden pendiente'),
(4, 'Confirmed', 'reservation', 'Reserva confirmada'),
(5, 'No Show', 'reservation', 'Cliente no asistio'),
(6, 'Cancelled', 'reservation', 'Reserva cancelada');

INSERT INTO fact_orders VALUES
(1001, 1, 1, 1, 20240105, 1, 2, 6500.0, 13000.0, 0.0, 13000.0, 1690.0, 14690.0, CAST('2024-01-05 12:30:00' AS TIMESTAMP), CAST('2024-01-05 13:00:00' AS TIMESTAMP)),
(1002, 2, 2, 2, 20240106, 1, 1, 7200.0, 7200.0, 500.0, 6700.0, 871.0, 7571.0, CAST('2024-01-06 19:15:00' AS TIMESTAMP), CAST('2024-01-06 19:50:00' AS TIMESTAMP)),
(1003, 1, 1, 5, 20240210, 1, 3, 2500.0, 7500.0, 0.0, 7500.0, 975.0, 8475.0, CAST('2024-02-10 09:10:00' AS TIMESTAMP), CAST('2024-02-10 09:25:00' AS TIMESTAMP)),
(1004, 3, 1, 3, 20240214, 1, 2, 4200.0, 8400.0, 0.0, 8400.0, 1092.0, 9492.0, CAST('2024-02-14 13:45:00' AS TIMESTAMP), CAST('2024-02-14 14:05:00' AS TIMESTAMP)),
(1005, 4, 3, 4, 20240303, 2, 1, 3800.0, 3800.0, 0.0, 3800.0, 494.0, 4294.0, CAST('2024-03-03 16:00:00' AS TIMESTAMP), CAST('2024-03-03 16:25:00' AS TIMESTAMP)),
(1006, 3, 2, 2, 20240315, 1, 2, 7200.0, 14400.0, 1000.0, 13400.0, 1742.0, 15142.0, CAST('2024-03-15 20:10:00' AS TIMESTAMP), CAST('2024-03-15 20:45:00' AS TIMESTAMP));

INSERT INTO fact_reservations VALUES
(2001, 1, 1, 20240105, 4, 4, 90, true, false, CAST('2024-01-05' AS DATE), CAST('2024-01-05 19:00:00' AS TIMESTAMP), CAST('2024-01-05 20:30:00' AS TIMESTAMP)),
(2002, 2, 2, 20240106, 4, 2, 75, true, false, CAST('2024-01-06' AS DATE), CAST('2024-01-06 18:30:00' AS TIMESTAMP), CAST('2024-01-06 19:45:00' AS TIMESTAMP)),
(2003, 3, 1, 20240214, 4, 5, 120, true, false, CAST('2024-02-14' AS DATE), CAST('2024-02-14 20:00:00' AS TIMESTAMP), CAST('2024-02-14 22:00:00' AS TIMESTAMP)),
(2004, 4, 3, 20240303, 5, 3, 90, false, true, CAST('2024-03-03' AS DATE), CAST('2024-03-03 12:00:00' AS TIMESTAMP), CAST('2024-03-03 13:30:00' AS TIMESTAMP)),
(2005, 1, 2, 20240315, 4, 6, 110, true, false, CAST('2024-03-15' AS DATE), CAST('2024-03-15 21:00:00' AS TIMESTAMP), CAST('2024-03-15 22:50:00' AS TIMESTAMP));
