USE restaurante_dw;

CREATE VIEW IF NOT EXISTS vw_ingresos_por_mes AS
SELECT
  t.anio,
  t.mes,
  SUM(f.total_orden) AS ingresos_totales,
  COUNT(f.id_orden) AS total_ordenes,
  SUM(f.cantidad_items) AS items_vendidos
FROM fact_ordenes f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
GROUP BY t.anio, t.mes;

CREATE VIEW IF NOT EXISTS vw_ventas_por_categoria AS
SELECT
  p.categoria,
  SUM(f.subtotal) AS ingresos_totales,
  SUM(f.cantidad) AS unidades_vendidas,
  COUNT(DISTINCT f.id_orden) AS ordenes_asociadas
FROM fact_detalle_ordenes f
JOIN dim_producto p ON f.id_producto = p.id_producto
GROUP BY p.categoria;

CREATE VIEW IF NOT EXISTS vw_ordenes_por_restaurante AS
SELECT
  r.id_restaurante,
  r.nombre_restaurante,
  COUNT(f.id_orden) AS total_ordenes,
  SUM(f.total_orden) AS ingresos_totales,
  AVG(f.total_orden) AS ticket_promedio
FROM fact_ordenes f
JOIN dim_restaurante r ON f.id_restaurante = r.id_restaurante
GROUP BY r.id_restaurante, r.nombre_restaurante;

CREATE VIEW IF NOT EXISTS vw_frecuencia_clientes AS
SELECT
  u.id_usuario,
  u.nombre_usuario,
  u.rol,
  COUNT(f.id_orden) AS total_ordenes,
  SUM(f.total_orden) AS gasto_total,
  AVG(f.total_orden) AS ticket_promedio
FROM fact_ordenes f
JOIN dim_usuario u ON f.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.nombre_usuario, u.rol;

CREATE VIEW IF NOT EXISTS vw_reservas_por_horario AS
SELECT
  t.dia_semana,
  t.hora,
  COUNT(f.id_reserva) AS total_reservas
FROM fact_reservas f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
GROUP BY t.dia_semana, t.hora;
