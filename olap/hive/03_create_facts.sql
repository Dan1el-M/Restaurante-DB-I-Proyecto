USE restaurante_dw;

CREATE TABLE IF NOT EXISTS fact_ordenes (
  id_orden INT,
  id_usuario INT,
  id_restaurante INT,
  id_mesa INT,
  id_tiempo INT,
  tipo_orden STRING,
  total_orden DECIMAL(10,2),
  cantidad_items INT
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS fact_detalle_ordenes (
  id_detalle_orden INT,
  id_orden INT,
  id_producto INT,
  id_usuario INT,
  id_restaurante INT,
  id_tiempo INT,
  cantidad INT,
  precio_unitario DECIMAL(10,2),
  subtotal DECIMAL(10,2)
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS fact_reservas (
  id_reserva INT,
  id_usuario INT,
  id_mesa INT,
  id_restaurante INT,
  id_tiempo INT,
  estado_reserva INT
)
STORED AS PARQUET;
