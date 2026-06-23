USE restaurante_dw;

CREATE TABLE IF NOT EXISTS dim_tiempo (
  id_tiempo INT,
  fecha DATE,
  dia INT,
  mes INT,
  trimestre INT,
  anio INT,
  hora INT,
  dia_semana STRING
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS dim_usuario (
  id_usuario INT,
  nombre_usuario STRING,
  rol STRING
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS dim_restaurante (
  id_restaurante INT,
  nombre_restaurante STRING,
  estado_restaurante INT,
  admin_id INT
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS dim_mesa (
  id_mesa INT,
  numero_mesa INT,
  estado_mesa INT,
  id_restaurante INT
)
STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS dim_producto (
  id_producto INT,
  nombre_producto STRING,
  categoria STRING,
  descripcion STRING,
  precio DECIMAL(10,2),
  id_restaurante INT
)
STORED AS PARQUET;
