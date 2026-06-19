# 🎨 DIAGRAMAS ARQUITECTÓNICOS

## 1. ARQUITECTURA GENERAL DEL DATA WAREHOUSE

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     DATA WAREHOUSE OLAP - ARQUITECTURA                   ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────┐
│     FUENTES DE DATOS            │
├─────────────────────────────────┤
│  PostgreSQL   │  MongoDB        │
│  ├─ Orders   │  ├─ Sessions    │
│  ├─ Users    │  ├─ Logs        │
│  └─ Tables   │  └─ Cache       │
└─────────────────────────────────┘
           ↓ (EXTRACCIÓN)
┌─────────────────────────────────┐
│    ETL PIPELINE (Python)        │
├─────────────────────────────────┤
│  extract_from_postgres()        │
│  extract_from_mongodb()         │
│  extract_from_hive()            │
└─────────────────────────────────┘
           ↓ (TRANSFORMACIÓN)
┌──────────────────────────────────────────────────────────────────┐
│              TRANSFORMACIÓN & LIMPIEZA                           │
├──────────────────────────────────────────────────────────────────┤
│  • Eliminar duplicados                                           │
│  • Rellenar valores nulos                                        │
│  • Crear claves naturales                                        │
│  • Calcular dimensiones temporales                               │
│  • Aggregaciones iniciales                                       │
└──────────────────────────────────────────────────────────────────┘
           ↓ (CARGA)
┌────────────────────────────────────────────────────────────────────┐
│              ALMACÉN DE DATOS (DATA WAREHOUSE) - HIVE              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          TABLAS DE DIMENSIONES                          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  dim_time       dim_customer      dim_product           │   │
│  │  dim_restaurant dim_status        (5 dimensiones)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          TABLAS DE HECHOS                               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  fact_orders     fact_reservations  (2 hechos)          │   │
│  │  (millones de registros)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
           ↓ (CREACIÓN DE VISTAS)
┌────────────────────────────────────────────────────────────────────┐
│                    CUBOS OLAP (VISTAS)                            │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Cubo 1: Ingresos por Mes y Categoría                 │    │
│  │  Cubo 2: Actividad de Clientes por Zona               │    │
│  │  Cubo 3: Órdenes Completadas vs Canceladas            │    │
│  │  Cubo 4: Tendencias de Horarios Pico                  │    │
│  │  Cubo 5: Crecimiento Mensual                          │    │
│  │  Cubo 6: Lealtad de Clientes                          │    │
│  │  Cubo 7: Bestsellers de Productos                     │    │
│  │  Cubo 8: Rendimiento por Restaurante                  │    │
│  │  Cubo 9: Ocupación de Mesas                           │    │
│  │  Cubo 10: Rentabilidad                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
           ↓ (DISPONIBLE PARA)
┌──────────────────────────────────────────────────────────────────┐
│            HERRAMIENTAS DE ANÁLISIS Y VISUALIZACIÓN              │
├──────────────────────────────────────────────────────────────────┤
│  • Superset/Metabase (Dashboards)                               │
│  • Tableau/Power BI (Reportes)                                  │
│  • Hive/SQL (Consultas ad-hoc)                                  │
│  • Python/Pandas (Data Science)                                 │
└──────────────────────────────────────────────────────────────────┘

Almacenamiento: Parquet (Compresión Columnar)
Formato: Hive Tables en HDFS
```

---

## 2. ESQUEMA ESTRELLA (STAR SCHEMA)

```
                          fact_orders
                      (Tabla de Hechos)
                     ╱    │    │    │   ╲
                   ╱      │    │    │    ╲
         ┌─────────────────┼────┼────┼─────────────────┐
         │                 │    │    │                 │
    dim_time         dim_customer dim_product    dim_restaurant
  (Dimensión          (Dimensión   (Dimensión    (Dimensión
    Temporal)           Cliente)     Producto)      Restaurante)
  ┌─────────┐         ┌──────────┐ ┌──────────┐  ┌─────────────┐
  │time_id  │         │cust_id   │ │prod_id   │  │rest_id      │
  │date     │         │name      │ │name      │  │name         │
  │month    │         │zone      │ │category  │  │location     │
  │year     │         │loyalty   │ │price     │  │zone         │
  │day_name │         │spent     │ │margin    │  │capacity     │
  └─────────┘         └──────────┘ └──────────┘  └─────────────┘
         ↓                 ↓             ↓                ↓
         │                 │             │                │
         └─────────────────┼─────────────┼────────────────┘
                           │
                    fact_reservations
                   (Tabla de Hechos 2)
                           │
                     dim_status
                   (Dimensión Estado)
                   ┌──────────────┐
                   │status_id     │
                   │status_name   │
                   │status_type   │
                   └──────────────┘
```

---

## 3. FLUJO DE DATOS EN TIEMPO REAL

```
HORA: 09:00 AM
┌─────────────────────────────────────────────────────────┐
│  Cliente: Juan García                                   │
│  Restaurante: San José Centro                           │
│  Hora: 09:00 AM - Lunes                                 │
│  Orden: Pizza + Bebida                                  │
└─────────────────────────────────────────────────────────┘
         ↓ Se guarda en PostgreSQL
         
HORA: Noche (ETL DIARIO)
┌─────────────────────────────────────────────────────────┐
│  ETL Pipeline Extrae:                                   │
│  • fact_orders: 1 fila (Pizza)                         │
│  • fact_orders: 1 fila (Bebida)                        │
│  • dim_customer: Juan García actualizado                │
│  • dim_time: 09:00 actualizado                         │
└─────────────────────────────────────────────────────────┘
         ↓ Transforma y carga a Hive
         
HORA: Mañana (07:00 AM)
┌─────────────────────────────────────────────────────────┐
│  Vistas OLAP Actualizadas:                              │
│  • cubo_ingresos_mes_categoria: +1 Pizza                │
│  • cubo_actividad_clientes_zona: +1 para San José       │
│  • cubo_lealtad_clientes: Juan actualizado              │
│  • cubo_horarios_pico: +2 a las 09:00 AM               │
│  • cubo_bestsellers_productos: Pizza subió             │
└─────────────────────────────────────────────────────────┘
         ↓ Disponible para análisis
         
RESULTADO EN DASHBOARD
┌─────────────────────────────────────────────────────────┐
│  Ingresos Lunes: +$15,000                              │
│  Cliente Activo: Juan García                            │
│  Horario Pico: 09:00 AM (20 órdenes)                   │
│  Bestseller: Pizza (250 vendidas esta semana)          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. MODELO DE DIMENSIONES

```
DIM_TIME (Análisis Temporal)
┌────────────────────────────────┐
│  Atributos:                    │
│  • time_id (PK)               │
│  • full_date                   │
│  • day_name (Lun, Mar, Mié...) │
│  • week_of_year                │
│  • month (1-12)                │
│  • month_name (Enero...)       │
│  • quarter (Q1-Q4)             │
│  • year (2024, 2025...)        │
│  • is_weekend (True/False)     │
│  • season (Verano, Invierno..) │
│                                │
│  Uso: Análisis por período     │
│       Tendencias, seasonalidad │
└────────────────────────────────┘

DIM_CUSTOMER (Análisis de Clientes)
┌────────────────────────────────┐
│  Atributos:                    │
│  • customer_id (PK)            │
│  • customer_name               │
│  • customer_type (Regular/VIP) │
│  • geographic_zone (Zona)      │
│  • loyalty_level (1-5)         │
│  • total_spent ($)             │
│  • total_orders (#)            │
│  • is_active (True/False)      │
│                                │
│  Uso: Segmentación de clientes │
│       Lealtad, valor de cliente│
└────────────────────────────────┘

DIM_PRODUCT (Análisis de Productos)
┌────────────────────────────────┐
│  Atributos:                    │
│  • product_id (PK)             │
│  • product_name                │
│  • category (Plato, Bebida..)  │
│  • subcategory                 │
│  • price ($)                   │
│  • cost ($)                    │
│  • margin (%)                  │
│  • is_available (True/False)   │
│                                │
│  Uso: Análisis de productos    │
│       Bestsellers, rentabilidad│
└────────────────────────────────┘

DIM_RESTAURANT (Análisis de Ubicaciones)
┌────────────────────────────────┐
│  Atributos:                    │
│  • restaurant_id (PK)          │
│  • restaurant_name             │
│  • location (Dirección)        │
│  • geographic_zone             │
│  • capacity (#mesas)           │
│  • status (Activo/Inactivo)    │
│                                │
│  Uso: Comparación entre sucurles│
│       Rendimiento por zona     │
└────────────────────────────────┘

DIM_STATUS (Análisis de Estados)
┌────────────────────────────────┐
│  Atributos:                    │
│  • status_id (PK)              │
│  • status_name                 │
│  • status_type (order/reserve) │
│  • description                 │
│                                │
│  Ejemplos de Valores:          │
│  1: Completada                 │
│  2: Cancelada                  │
│  3: Pendiente                  │
│  4: No Show                    │
│                                │
│  Uso: Filtros por estado       │
│       Análisis de calidad      │
└────────────────────────────────┘
```

---

## 5. MODELO DE HECHOS

```
FACT_ORDERS (Hechos de Órdenes)
┌─────────────────────────────────────────────┐
│  Claves (Dimensiones):                      │
│  • order_id (PK)                            │
│  • customer_id (FK) → dim_customer          │
│  • restaurant_id (FK) → dim_restaurant      │
│  • product_id (FK) → dim_product            │
│  • time_id (FK) → dim_time                  │
│  • status_id (FK) → dim_status              │
│                                             │
│  Métricas (Medidas):                        │
│  • quantity (#items)                        │
│  • unit_price ($)                           │
│  • total_amount ($)                         │
│  • net_amount ($)                           │
│  • tax_amount ($)                           │
│  • final_amount ($)                         │
│  • discount ($)                             │
│                                             │
│  Granularidad: 1 fila = 1 item de orden    │
│  Ejemplo:                                   │
│  Orden #100 contiene:                       │
│    - 1 Pizza ($10) → 1 fila                │
│    - 1 Bebida ($2) → 1 fila                │
│    - 1 Postre ($3) → 1 fila                │
│  Total: 3 filas en fact_orders             │
└─────────────────────────────────────────────┘

FACT_RESERVATIONS (Hechos de Reservas)
┌─────────────────────────────────────────────┐
│  Claves (Dimensiones):                      │
│  • reservation_id (PK)                      │
│  • customer_id (FK) → dim_customer          │
│  • restaurant_id (FK) → dim_restaurant      │
│  • time_id (FK) → dim_time                  │
│  • status_id (FK) → dim_status              │
│                                             │
│  Métricas (Medidas):                        │
│  • party_size (#personas)                   │
│  • duration_minutes (minutos)               │
│  • table_occupied (True/False)              │
│  • no_show (True/False)                     │
│  • check_in_time (timestamp)                │
│  • check_out_time (timestamp)               │
│                                             │
│  Granularidad: 1 fila = 1 reservación      │
└─────────────────────────────────────────────┘
```

---

## 6. CICLO DE VIDA DE UN DATO

```
FASE 1: ORIGEN (Operacional)
┌─────────────────────────────┐
│ Cliente ordena:             │
│ - Pizza $10                 │
│ - Bebida $2                 │
│ Hora: 09:00 AM Lunes 15     │
│ Restaurante: San José       │
└─────────────────────────────┘
        ↓ Se guarda en
        
FASE 2: CAPTURA (PostgreSQL)
┌──────────────────────────────────┐
│ Tabla: orders                    │
│ order_id: 100                    │
│ customer_id: 5                   │
│ restaurant_id: 1                 │
│ order_date: 2024-01-15 09:00     │
└──────────────────────────────────┘
        ↓ ETL extrae de noche
        
FASE 3: TRANSFORMACIÓN (Python)
┌──────────────────────────────────┐
│ 1. Extrae de PostgreSQL          │
│ 2. Busca al cliente en MongoDB   │
│ 3. Calcula impuestos 13%         │
│ 4. Asigna dim_time (day=Monday)  │
│ 5. Calcula margen de producto    │
└──────────────────────────────────┘
        ↓ Carga a Hive
        
FASE 4: ALMACENAMIENTO (Hive)
┌─────────────────────────────────────────┐
│ fact_orders:                            │
│ Row 1: order_id=100, product_id=3,      │
│        quantity=1, unit_price=10,       │
│        final_amount=11.30               │
│                                         │
│ Row 2: order_id=100, product_id=5,      │
│        quantity=1, unit_price=2,        │
│        final_amount=2.26                │
│                                         │
│ dim_customer: customer_id=5 actualizado │
│ dim_time: time_id=15 actualizado        │
└─────────────────────────────────────────┘
        ↓ Crea vistas
        
FASE 5: ANÁLISIS (Cubos OLAP)
┌──────────────────────────────────┐
│ cubo_ingresos_mes_categoria:     │
│ month: Enero, categoria: Pizza   │
│ ingresos: +$10 (+ IVA)           │
│ ordenes: +1                      │
│                                  │
│ cubo_horarios_pico:              │
│ dia: Lunes, hora: 09:00          │
│ ordenes_por_hora: +1             │
│                                  │
│ cubo_bestsellers:                │
│ pizza: +1 venta                  │
│ ingresos: +$10                   │
└──────────────────────────────────┘
        ↓ Dashboard muestra
        
FASE 6: VISUALIZACIÓN (BI Tools)
┌──────────────────────────────────┐
│ 📊 Dashboard Enero 2024:         │
│                                  │
│ Ingresos: $45,320                │
│ Órdenes: 1,240                   │
│ Ticket Promedio: $36.50          │
│                                  │
│ Bestsellers:                     │
│ 1. Pizza - 320 vendidas          │
│ 2. Pasta - 180 vendidas          │
│                                  │
│ Horario Pico: 13:00 (Almuerzo)  │
│ Zona Activa: San José            │
└──────────────────────────────────┘
```

---

## 7. COMPARACIÓN: OLTP vs OLAP

```
┌─────────────────────────────────────────────────────────────┐
│              OLTP (Operacional)  vs  OLAP (Analítico)       │
├────────────────────────┬────────────────────────────────────┤
│  Característica        │  OLTP      │  OLAP                │
├────────────────────────┼────────────┼────────────────────────┤
│  Base de Datos         │  PostgreSQL│  Hive / Data Warehouse│
│  Propósito             │  Producción│  Análisis             │
│  Usuarios              │  Sistemas  │  Analistas / BI       │
│  Consultas             │  Simples   │  Complejas            │
│  Actualización         │  Continua  │  Noche (ETL)          │
│  Datos Históricos      │  Últimos   │  5+ años              │
│  Normalización         │  Altamente │  Desnormalizado       │
│  Volumen               │  GB        │  TB/PB                │
│  Velocidad             │  Rápida    │  Muy rápida en lectura│
│  Redundancia           │  Baja      │  Alta (pre-calculado) │
│  Latencia              │  Real-time │  Horas/Días           │
└────────────────────────┴────────────┴────────────────────────┘
```

---

**Creado para**: Base de Datos II - Proyecto OLAP
**Versión**: 1.0
**Actualizado**: 2024
