#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAREHOUSE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# Data Warehouse OLAP - Script de Inicialización
# Base de Datos II - Proyecto OLAP

echo "╔═══════════════════════════════════════════════════════╗"
echo "║     Data Warehouse OLAP - Script de Inicialización   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Verificar si Hive está disponible
if ! command -v hive &> /dev/null; then
    echo "❌ Hive no está instalado o no está en PATH"
    echo "   Instálalo con: hadoop fs -ls hdfs://localhost:9000"
    exit 1
fi

echo "✓ Hive detectado"
echo ""

# Paso 1: Crear el esquema estrella
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 1: Creando esquema ESTRELLA..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

hive -f "$WAREHOUSE_DIR/schemas/schema_star.sql"
if [ $? -eq 0 ]; then
    echo "✓ Esquema creado exitosamente"
else
    echo "❌ Error al crear el esquema"
    exit 1
fi

echo ""

# Paso 2: Crear las vistas OLAP
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 2: Creando vistas OLAP..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

hive -f "$WAREHOUSE_DIR/schemas/hive_olap_views.sql"
if [ $? -eq 0 ]; then
    echo "✓ Vistas OLAP creadas exitosamente"
else
    echo "❌ Error al crear las vistas"
    exit 1
fi

echo ""

# Paso 3: Ejecutar ETL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 3: Ejecutando ETL Pipeline..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python "$WAREHOUSE_DIR/etl/etl_pipeline.py"
if [ $? -eq 0 ]; then
    echo "✓ ETL completado exitosamente"
else
    echo "❌ Error en ETL"
    exit 1
fi

echo ""

# Paso 4: Verificar tablas creadas
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 4: Verificando tablas y vistas..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

hive -e "SHOW TABLES;" | grep -E "(dim_|fact_|cubo_)"
echo ""
hive -e "SHOW VIEWS;" | grep "cubo_"

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║        ✓ Data Warehouse OLAP Inicializado            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "📊 Próximos pasos:"
echo "   1. Cargar datos usando: python $WAREHOUSE_DIR/etl/etl_pipeline.py"
echo "   2. Consultar con Hive: hive"
echo "   3. Luego: SELECT * FROM cubo_ingresos_mes_categoria LIMIT 5;"
echo ""
