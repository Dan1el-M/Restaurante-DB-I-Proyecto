# GUÍA COMPLETA: Data Warehouse OLAP
# Base de Datos II - Proyecto OLAP - Punto 1
# Universidad Tecnológica de Costa Rica

---

## 📊 RESUMEN EJECUTIVO

Este documento detalla la implementación de un **Data Warehouse OLAP** con esquema estrella para análisis multidimensional de datos del sistema de restaurante.

**Objetivo**: Consolidar datos históricos de reservas, pedidos, productos y usuarios en una estructura optimizada para análisis rápidos.

---

## 🏗️ COMPONENTES PRINCIPALES

### 1. TABLAS DE DIMENSIONES (5 tablas)

Las dimensiones son contextos que describen los hechos:

```
dim_time              dim_customer          dim_product
├─ time_id           ├─ customer_id        ├─ product_id
├─ full_date         ├─ customer_name      ├─ product_name
├─ day_name          ├─ geographic_zone    ├─ category
├─ month             ├─ loyalty_level      ├─ price
├─ year              ├─ total_spent        └─ margin
└─ season            └─ total_orders

dim_restaurant        dim_status
├─ restaurant_id     ├─ status_id
├─ restaurant_name   ├─ status_name
├─ location          ├─ status_type
├─ geographic_zone   └─ description
└─ capacity
```

**¿Por qué?**
- Permiten filtrar datos de múltiples formas
- Se actualizan lentamente (cambios poco frecuentes)
- Facilitan análisis complejos sin recalcular

### 2. TABLAS DE HECHOS (2 tablas)

Los hechos contienen métricas cuantificables:

```
fact_orders                          fact_reservations
├─ order_id (PK)                     ├─ reservation_id (PK)
├─ customer_id (FK)                  ├─ customer_id (FK)
├─ restaurant_id (FK)                ├─ restaurant_id (FK)
├─ product_id (FK)                   ├─ time_id (FK)
├─ time_id (FK)                      ├─ status_id (FK)
├─ status_id (FK)                    ├─ party_size (métrica)
├─ quantity (métrica)                ├─ duration_minutes (métrica)
├─ total_amount (métrica)            ├─ table_occupied (métrica)
└─ final_amount (métrica)            └─ no_show (métrica)
```

**¿Por qué?**
- Almacenan lo que realmente importa (ventas, ingresos, reservas)
- Muchas filas, pocas columnas
- Conectan dimensiones para análisis multidimensional

### 3. RELACIONES ENTRE TABLAS

```
                   fact_orders
                   /  |  |  \
                  /   |  |   \
        dim_customer dim_time dim_product
                  \   |  |   /
                   \  |  |  /
                   dim_restaurant
                      |
                  dim_status
```

---

## 🧮 EJEMPLO: ANÁLISIS DE INGRESOS POR MES Y CATEGORÍA

**Pregunta**: "¿Cuántos ingresos tuvimos por cada categoría de producto cada mes?"

### Sin Data Warehouse (Lento):
```sql
SELECT 
    DATE_TRUNC('month', o.order_time),
    m.category,
    SUM(oi.price * oi.quantity)
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN menus m ON oi.menu_id = m.menu_id
GROUP BY DATE_TRUNC('month', o.order_time), m.category;
-- ⚠️ Debe recalcular CADA VEZ
-- ⚠️ Recorre millones de registros
```

### Con Data Warehouse (Rápido):
```sql
SELECT year, month_name, category, ingresos_totales
FROM cubo_ingresos_mes_categoria
WHERE year = 2024;
-- ✓ Resultado PRE-CALCULADO
-- ✓ Consulta instantánea
-- ✓ Solo consulta dimensiones agregadas
```

**Ventaja**: ~1000x más rápido

---

## 📈 FLUJO DE DATOS (ETL)

```
PostgreSQL/MongoDB (Datos Originales)
         ↓
    EXTRACCIÓN
         ↓
   TRANSFORMACIÓN
   ├─ Limpieza
   ├─ Validación
   └─ Agregación
         ↓
  CARGA EN HIVE
   ├─ dim_time
   ├─ dim_customer
   ├─ dim_product
   ├─ dim_restaurant
   ├─ dim_status
   ├─ fact_orders
   └─ fact_reservations
         ↓
  VISTAS OLAP (Cubos)
   ├─ cubo_ingresos_mes_categoria
   ├─ cubo_actividad_clientes_zona
   ├─ cubo_ordenes_completadas_canceladas
   ├─ cubo_tendencias_horarios_pico
   ├─ cubo_crecimiento_mensual
   ├─ cubo_lealtad_clientes
   ├─ cubo_bestsellers_productos
   ├─ cubo_rendimiento_restaurantes
   ├─ cubo_ocupacion_mesas
   └─ cubo_rentabilidad
         ↓
  DISPONIBLE PARA ANÁLISIS
  (Superset, Tableau, Power BI, etc.)
```

---

## 🔍 LOS 10 CUBOS OLAP EXPLICADOS

### Cubo 1: Ingresos por Mes y Categoría
```
Dimensiones: Mes, Categoría de Producto
Métricas:    Ingresos, Órdenes, Margen

Uso: ¿Cuál es el producto más rentable cada mes?
```

### Cubo 2: Actividad de Clientes por Zona
```
Dimensiones: Zona Geográfica, Restaurante
Métricas:    Clientes Únicos, Órdenes, Reservas

Uso: ¿Cuáles zonas son más activas?
```

### Cubo 3: Órdenes Completadas vs Canceladas
```
Dimensiones: Mes, Estado de Orden
Métricas:    Cantidad, Monto, Porcentaje

Uso: ¿Cuál es la tasa de cancelación?
```

### Cubo 4: Horarios Pico de Venta
```
Dimensiones: Hora del Día, Día de Semana, Categoría
Métricas:    Órdenes por Hora, Ingresos

Uso: ¿Cuándo vendemos más?
```

### Cubo 5: Crecimiento Mensual
```
Dimensiones: Mes, Restaurante
Métricas:    Crecimiento %, Clientes Nuevos

Uso: ¿Cómo crece el negocio mes a mes?
```

### Cubo 6: Lealtad de Clientes
```
Dimensiones: Cliente, Tipo de Cliente
Métricas:    Gasto Total, Frecuencia de Compra

Uso: ¿Quiénes son nuestros clientes más leales?
```

### Cubo 7: Bestsellers de Productos
```
Dimensiones: Producto, Categoría
Métricas:    Veces Vendido, Ingresos, Ganancia

Uso: ¿Cuáles son los productos estrella?
```

### Cubo 8: Rendimiento por Restaurante
```
Dimensiones: Restaurante, Zona Geográfica
Métricas:    Ingresos, Ocupación, No-Shows

Uso: ¿Cuál restaurante va mejor?
```

### Cubo 9: Ocupación de Mesas
```
Dimensiones: Restaurante, Día, Mes
Métricas:    Ocupación %, Duración Promedio

Uso: ¿Qué tan ocupadas están las mesas?
```

### Cubo 10: Rentabilidad
```
Dimensiones: Restaurante, Mes
Métricas:    Margen %, Ganancia Bruta

Uso: ¿Cuál es el margen de ganancia?
```

---

## 💾 ARCHIVOS GENERADOS

```
dataW/warehouse/
├─ schemas/schema_star.sql  ← Crea tablas (dim_ y fact_)
├─ schemas/hive_olap_views.sql ← Crea 10 cubos OLAP
├─ etl/etl_pipeline.py      ← Script de carga de datos
├─ tests/test_queries.py    ← Consultas de ejemplo
├─ scripts/init_warehouse.sh← Script de inicialización
├─ config/requirements.txt  ← Dependencias Python
└─ explicaciones/README.md ← Documentación
```

---

## 🚀 CÓMO USAR

### Paso 1: Crear Esquema
```bash
cd dataW/warehouse
hive -f schemas/schema_star.sql
```

### Paso 2: Crear Vistas OLAP
```bash
hive -f schemas/hive_olap_views.sql
```

### Paso 3: Cargar Datos (ETL)
```bash
python etl/etl_pipeline.py
```

### Paso 4: Consultar
```bash
hive
> SELECT * FROM cubo_ingresos_mes_categoria LIMIT 10;
> SELECT * FROM cubo_bestsellers_productos ORDER BY ingresos_producto DESC;
```

---

## 📊 EJEMPLO DE ANÁLISIS REAL

**Pregunta**: "¿Cuáles fueron los 5 productos más rentables en 2024?"

```sql
SELECT 
    product_name,
    category,
    veces_vendido,
    ingresos_producto,
    ganancia_total,
    ROUND((ganancia_total / ingresos_producto * 100), 2) as margen_pct
FROM cubo_bestsellers_productos
WHERE ranking_categoria <= 5
ORDER BY ganancia_total DESC;
```

**Resultado esperado**:
```
product_name       category    veces_vendido  ingresos  ganancia   margen_pct
─────────────────────────────────────────────────────────────────────────────
Pizza Margherita   Platos      1250           75000     22500      30%
Pasta Carbonara    Platos      950            71250     21375      30%
Cerveza Premium    Bebidas     2100           31500     18900      60%
Tiramisu           Postres     750            22500     13500      60%
Agua Mineral       Bebidas     5000           5000      3000       60%
```

---

## 🔧 CONFIGURACIONES IMPORTANTES

### Índices Creados
```sql
CREATE INDEX idx_fact_orders_time ON fact_orders(time_id);
CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_fact_orders_restaurant ON fact_orders(restaurant_id);
CREATE INDEX idx_fact_orders_status ON fact_orders(status_id);
```

**Beneficio**: Consultas 10-100x más rápidas

### Formatos de Almacenamiento
- **Parquet** (Recomendado): Compresión columnar, perfecto para OLAP
- **ORC**: Formato optimizado de Hive, también muy eficiente
- **CSV**: Para exportación e integración con otras herramientas

---

## 📈 MÉTRICAS SOPORTADAS

### Financieras
- Ingresos brutos
- Ingresos netos
- Ganancia bruta
- Margen de ganancia (%)
- Costo de productos

### Operacionales
- Cantidad de órdenes
- Cantidad de reservas
- Ocupación de mesas (%)
- Duración promedio
- Tasa de no-show (%)

### De Cliente
- Cliente activos
- Gasto total por cliente
- Frecuencia de compra
- Nivel de lealtad
- Tipo de cliente

---

## ⚠️ CONSIDERACIONES IMPORTANTES

1. **Actualización**: ETL debe ejecutarse diariamente (o según frecuencia del negocio)
2. **Granularidad**: Cada fila en fact_orders = 1 item (no 1 orden)
3. **SCD Type 1**: Las dimensiones no guardan historial (se sobrescriben)
4. **Rendimiento**: Todas las vistas usan agregaciones pre-calculadas
5. **Escalabilidad**: Diseñado para crecer con Apache Hive en cluster Hadoop

---

## 🎯 PRÓXIMOS PASOS (Otros Puntos del Proyecto)

Después de completar el Data Warehouse:

1. **Punto 2**: Apache Spark para transformaciones complejas
2. **Punto 3**: Visualización con Superset/Metabase
3. **Punto 4**: Orquestación con Apache Airflow
4. **Punto 5**: Análisis con Neo4J (grafos)
5. **Punto 6**: Rutas de entrega optimizadas

---

## 📞 VALIDACIÓN

Para verificar que todo funciona:

```bash
# 1. Verificar tablas creadas
hive -e "SHOW TABLES LIKE 'dim_%';"

# 2. Verificar hechos creados
hive -e "SHOW TABLES LIKE 'fact_%';"

# 3. Verificar vistas OLAP
hive -e "SHOW VIEWS LIKE 'cubo_%';"

# 4. Contar registros en cada tabla
hive -e "SELECT COUNT(*) FROM dim_time;"
hive -e "SELECT COUNT(*) FROM fact_orders;"
```

---

**Documentación creada**: 2024
**Estado**: ✓ Punto 1 Completado
**Siguiente**: Punto 2 - Apache Spark
