# Spark Analytics - Punto 2

Esta carpeta contiene la implementacion del procesamiento analitico con Apache Spark.

## Objetivo

El punto 2 pide procesar grandes volumenes de datos de ordenes, productos y reservas usando:

- Spark DataFrames.
- SparkSQL.
- Al menos tres analisis: tendencias de consumo, horarios pico y crecimiento mensual.

## Archivos

- `jobs/analytics_job.py`: job PySpark principal. Genera datos de prueba escalables, crea DataFrames, ejecuta transformaciones y guarda resultados.
- `tests/run_full_spark_validation.ps1`: prueba automatica para levantar Spark desde Docker Compose, ejecutar el job y validar que produjo resultados.
- `output/`: carpeta generada por el job con los CSV de resultados y un resumen JSON.

## Ejecucion rapida

```powershell
.\dataW\spark\tests\run_full_spark_validation.ps1
```

Por defecto Docker Compose usa una version pinneada y verificada de Apache Spark:
`apache/spark:3.5.5-scala2.12-java17-python3-ubuntu`.
Si se necesita cambiar de imagen, usar siempre un tag explicito y nunca `latest`:

```powershell
$env:SPARK_IMAGE="apache/spark:3.5.5-scala2.12-java17-python3-ubuntu"
docker compose up -d spark-master spark-worker
```

## Salidas generadas

- `output/consumption_trends`: tendencias de consumo por tiempo, producto y categoria.
- `output/peak_hours`: horarios pico por dia, hora y categoria.
- `output/monthly_growth`: crecimiento mensual de ordenes, ingresos y reservas.
- `output/validation_summary.json`: conteos de entrada y salida para evidencia.
