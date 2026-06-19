# Data Warehouse OLAP - Proyecto Base de Datos II

## 📊 Descripción General

Este componente implementa un **Data Warehouse OLAP** para análisis multidimensional de datos del sistema de restaurante. Utiliza un **esquema estrella** optimizado para consultas analíticas rápidas.

---

## 🏗️ Arquitectura del Data Warehouse

### Diagrama del Esquema Estrella

```
                        fact_orders
                            ↙ ↓ ↘
                    ┌────────┼─┼────────┐
                    ↓        ↓ ↓        ↓
            dim_customer  dim_time  dim_product
                         ↓         ↓
                  dim_restaurant  dim_status

            fact_reservations
                    ↙ ↓ ↘
            ┌────────┼─┼────────┐
            ↓        ↓ ↓        ↓
        dim_customer dim_time  dim_restaurant
                         ↓
                  dim_status
```

---

## 📁 Componentes Principales

### 1. **Tablas de Dimensiones**

#### `dim_time` (Dimensión Temporal)
- **Propósito**: Análisis por período temporal
- **Campos clave**: 
  - `time_id`: ID único
  - `full_date`, `month`, `year`, `quarter`
  - `day_name`, `is_weekend`, `season`
- **Uso**: Filtros por fecha, tendencias temporales

#### `dim_customer` (Dimensión Cliente)
- **Propósito**: Información sobre clientes y su comportamiento
- **Campos clave**:
  - `customer_id`: ID único
  - `geographic_zone`: Zona geográfica
  - `customer_type`: Regular, VIP, etc.
  - `loyalty_level`: Nivel de lealtad
  - `total_spent`, `total_orders`
- **Uso**: Segmentación de clientes, análisis de lealtad

#### `dim_product` (Dimensión Producto)
- **Propósito**: Información sobre productos/menús
- **Campos clave**:
  - `product_id`: ID único
  - `category`, `subcategory`: Clasificación
  - `price`, `cost`, `margin`: Valores financieros
- **Uso**: Análisis de bestsellers, rentabilidad por producto

#### `dim_restaurant` (Dimensión Restaurante)
- **Propósito**: Información sobre ubicaciones
- **Campos clave**:
  - `restaurant_id`: ID único
  - `geographic_zone`: Zona geográfica
  - `location`: Ubicación exacta
  - `capacity`: Capacidad de mesas
- **Uso**: Análisis por ubicación, comparativas entre restaurantes

#### `dim_status` (Dimensión Estado)
- **Propósito**: Estados posibles de órdenes y reservas
- **Campos clave**:
  - `status_id`: ID único
  - `status_name`: Nombre del estado
  - `status_type`: 'order' o 'reservation'
- **Uso**: Filtros por estado, análisis de completitud

---

### 2. **Tablas de Hechos**

#### `fact_orders` (Hechos de Órdenes)
- **Propósito**: Métricas de cada orden
- **Campos clave**:
  - `order_id`: ID único
  - `quantity`, `unit_price`: Detalles de venta
  - `total_amount`, `net_amount`, `final_amount`: Financieros
  - Claves foráneas a todas las dimensiones
- **Granularidad**: 1 fila por item de orden

#### `fact_reservations` (Hechos de Reservaciones)
- **Propósito**: Métricas de cada reservación
- **Campos clave**:
  - `reservation_id`: ID único
  - `party_size`: Número de personas
  - `duration_minutes`: Duración de reserva
  - `table_occupied`, `no_show`: Estados
  - Claves foráneas a dimensiones
- **Granularidad**: 1 fila por reservación

---

## 🔍 Cubos OLAP (Vistas Analíticas)

### Disponibles:

| # | Cubo | Dimensiones | Métricas |
|---|------|------------|---------|
| 1 | **Ingresos por Mes y Categoría** | Tiempo, Producto | Ingresos, Órdenes, Margen |
| 2 | **Actividad Clientes por Zona** | Cliente, Restaurante | Clientes únicos, Órdenes, Reservas |
| 3 | **Órdenes Completadas vs Canceladas** | Tiempo, Estado | Cantidad, Monto, Porcentaje |
| 4 | **Tendencias y Horarios Pico** | Tiempo, Producto | Órdenes por hora, Ingresos |
| 5 | **Crecimiento Mensual** | Tiempo, Restaurante | Crecimiento %, Clientes nuevos |
| 6 | **Lealtad de Clientes** | Cliente | Gasto total, Frecuencia de compra |
| 7 | **Bestsellers de Productos** | Producto | Veces vendido, Ganancia |
| 8 | **Rendimiento por Restaurante** | Restaurante | Ingresos, No-shows, Ocupación |
| 9 | **Ocupación de Mesas** | Tiempo, Restaurante | % Ocupación, Duración promedio |
| 10 | **Rentabilidad** | Tiempo, Restaurante | Margen %, Ganancia bruta |

---

## 🔄 Pipeline ETL

### Fases:

```
EXTRACCIÓN (PostgreSQL/MongoDB)
    ↓
TRANSFORMACIÓN (Limpieza, Agregación)
    ↓
CARGA (Apache Hive - Parquet)
    ↓
ACTUALIZACIÓN DE VISTAS OLAP
    ↓
DISPONIBLE PARA CONSULTAS
```

### Archivo: `etl/etl_pipeline.py`

**Clase**: `WarehouseETL`

**Métodos principales**:
- `extract_from_postgres()`: Extrae de PostgreSQL
- `extract_from_mongodb()`: Extrae de MongoDB
- `create_dim_*()`: Crea dimensiones
- `create_fact_*()`: Crea tablas de hechos
- `load_to_hive()`: Carga a Hive (Parquet/CSV/ORC)
- `run_full_etl()`: Ejecuta pipeline completo

---

## 📋 Esquema SQL

### Archivo: `schemas/schema_star.sql`

Contiene:
- Definición de todas las dimensiones
- Definición de tablas de hechos
- Claves foráneas y restricciones
- Índices para optimización

**Uso**:
```bash
hive -f schemas/schema_star.sql
```

---

## 📊 Vistas OLAP

### Archivo: `schemas/hive_olap_views.sql`

Contiene 10 vistas OLAP pre-configuradas para:
- Análisis de ingresos
- Análisis de clientes
- Análisis de productos
- Análisis de rendimiento
- Análisis de rentabilidad

**Uso**:
```bash
hive -f schemas/hive_olap_views.sql
```

**Ejemplo de consulta**:
```sql
SELECT * FROM cubo_ingresos_mes_categoria 
WHERE year = 2024 AND category = 'Bebidas'
ORDER BY ingresos_totales DESC;
```

---

## 🚀 Cómo Usar

### 1. **Crear el esquema**
```bash
cd dataW/warehouse
hive -f schemas/schema_star.sql
```

### 2. **Crear las vistas OLAP**
```bash
hive -f schemas/hive_olap_views.sql
```

### 3. **Ejecutar el ETL**
```bash
python etl/etl_pipeline.py
```

### 4. **Consultar los datos**
```bash
hive
> SELECT * FROM cubo_ingresos_mes_categoria LIMIT 10;
> SELECT * FROM cubo_lealtad_clientes;
> SELECT * FROM cubo_bestsellers_productos ORDER BY ingresos_producto DESC LIMIT 10;
```

---

## 📈 Ejemplos de Análisis

### Análisis 1: Ingresos por Mes
```sql
SELECT 
    year, 
    month_name, 
    SUM(ingresos_totales) as ingresos,
    COUNT(total_ordenes) as ordenes
FROM cubo_ingresos_mes_categoria
GROUP BY year, month_name
ORDER BY year, month;
```

### Análisis 2: Top 10 Productos
```sql
SELECT 
    product_name,
    category,
    veces_vendido,
    ingresos_producto,
    ganancia_total,
    ranking_categoria
FROM cubo_bestsellers_productos
WHERE ranking_categoria <= 10
ORDER BY ingresos_producto DESC;
```

### Análisis 3: Clientes por Zona
```sql
SELECT 
    geographic_zone,
    total_clientes_unicos,
    total_ordenes,
    ingresos_zona,
    ticket_promedio
FROM cubo_actividad_clientes_zona
ORDER BY ingresos_zona DESC;
```

### Análisis 4: Rentabilidad por Restaurante
```sql
SELECT 
    restaurant_name,
    year,
    month_name,
    ingresos_brutos,
    ganancia_bruta,
    margen_porcentaje
FROM cubo_rentabilidad
WHERE year = 2024
ORDER BY margen_porcentaje DESC;
```

---

## 🔧 Configuración y Optimización

### Índices Incluidos
- `idx_fact_orders_time`: Optimiza filtros por fecha
- `idx_fact_orders_customer`: Optimiza filtros por cliente
- `idx_fact_orders_restaurant`: Optimiza filtros por restaurante
- `idx_fact_orders_status`: Optimiza filtros por estado

### Formatos de Almacenamiento
- **Parquet**: Compresión columnar (Recomendado)
- **ORC**: Formato optimizado para Hive
- **CSV**: Para exportación e integración

---

## 📝 Notas Importantes

1. **Granularidad**: Cada fila en `fact_orders` = 1 item de una orden
2. **Dimensiones Congeladas**: No cambian con el tiempo (SCD Type 1)
3. **Agregaciones Pre-calculadas**: Vistas OLAP contienen métricas agregadas
4. **Actualización**: ETL debe ejecutarse periódicamente (diariamente recomendado)
5. **Escalabilidad**: Diseñado para crecer con Apache Hive

---

## 🤝 Integraciones

Este Data Warehouse se integra con:
- **Apache Spark**: Para transformaciones complejas
- **Apache Airflow**: Para orquestación del ETL
- **Apache Superset/Metabase**: Para visualización
- **Neo4J**: Para análisis de grafos

---

## 📞 Soporte

Para preguntas sobre el Data Warehouse:
1. Revisar este README
2. Consultar `schemas/schema_star.sql` para estructura
3. Consultar `schemas/hive_olap_views.sql` para vistas disponibles
4. Ejecutar `etl/etl_pipeline.py` con logging activado

---

**Última actualización**: 2024
**Versión**: 1.0
