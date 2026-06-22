"""
Job PySpark para el punto 2 del proyecto.

Este archivo demuestra el uso de Spark DataFrames y SparkSQL sobre datos de
ordenes, productos y reservas. El job genera un dataset de prueba escalable,
ejecuta los tres analisis requeridos y guarda evidencia en archivos CSV/JSON.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


# Rutas usadas dentro del contenedor Spark. Docker Compose monta dataW/spark en
# /workspace/spark para que las salidas queden disponibles en el host.
SPARK_ROOT = Path(os.getenv("SPARK_ANALYTICS_ROOT", "/workspace/spark"))
OUTPUT_DIR = SPARK_ROOT / "output"


def build_spark_session() -> SparkSession:
    """Crea la sesion Spark usada por todo el job."""
    return (
        SparkSession.builder.appName("RestaurantSparkAnalytics")
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "4"))
        .getOrCreate()
    )


def clean_output_dir() -> None:
    """Limpia salidas previas para que cada ejecucion deje evidencia fresca."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_base_dataframes(spark: SparkSession) -> dict:
    """Crea DataFrames base equivalentes a dimensiones y hechos del DW."""
    time_schema = StructType(
        [
            StructField("time_id", IntegerType(), False),
            StructField("full_date", StringType(), False),
            StructField("day_name", StringType(), False),
            StructField("month", IntegerType(), False),
            StructField("month_name", StringType(), False),
            StructField("quarter", IntegerType(), False),
            StructField("year", IntegerType(), False),
        ]
    )
    time_rows = [
        (20240105, "2024-01-05", "Friday", 1, "January", 1, 2024),
        (20240106, "2024-01-06", "Saturday", 1, "January", 1, 2024),
        (20240210, "2024-02-10", "Saturday", 2, "February", 1, 2024),
        (20240214, "2024-02-14", "Wednesday", 2, "February", 1, 2024),
        (20240303, "2024-03-03", "Sunday", 3, "March", 1, 2024),
        (20240315, "2024-03-15", "Friday", 3, "March", 1, 2024),
    ]

    product_schema = StructType(
        [
            StructField("product_id", IntegerType(), False),
            StructField("product_name", StringType(), False),
            StructField("category", StringType(), False),
            StructField("subcategory", StringType(), False),
            StructField("price", DoubleType(), False),
            StructField("cost", DoubleType(), False),
        ]
    )
    product_rows = [
        (1, "Hamburguesa Clasica", "Plato fuerte", "Hamburguesas", 6500.0, 3200.0),
        (2, "Pizza Margarita", "Plato fuerte", "Pizzas", 7200.0, 3600.0),
        (3, "Ensalada Verde", "Entrada", "Ensaladas", 4200.0, 1800.0),
        (4, "Cheesecake", "Postre", "Dulces", 3800.0, 1500.0),
        (5, "Cafe Frio", "Bebida", "Cafe", 2500.0, 900.0),
    ]

    restaurant_schema = StructType(
        [
            StructField("restaurant_id", IntegerType(), False),
            StructField("restaurant_name", StringType(), False),
            StructField("location", StringType(), False),
            StructField("geographic_zone", StringType(), False),
            StructField("capacity", IntegerType(), False),
        ]
    )
    restaurant_rows = [
        (1, "Restaurante Central", "San Jose", "Central", 80),
        (2, "Restaurante Oeste", "Escazu", "Oeste", 60),
        (3, "Restaurante Este", "Cartago", "Este", 45),
    ]

    order_schema = StructType(
        [
            StructField("order_id", IntegerType(), False),
            StructField("customer_id", IntegerType(), False),
            StructField("restaurant_id", IntegerType(), False),
            StructField("product_id", IntegerType(), False),
            StructField("time_id", IntegerType(), False),
            StructField("quantity", IntegerType(), False),
            StructField("final_amount", DoubleType(), False),
            StructField("order_time_text", StringType(), False),
        ]
    )
    order_rows = [
        (1001, 1, 1, 1, 20240105, 2, 14690.0, "2024-01-05 12:30:00"),
        (1002, 2, 2, 2, 20240106, 1, 7571.0, "2024-01-06 19:15:00"),
        (1003, 1, 1, 5, 20240210, 3, 8475.0, "2024-02-10 09:10:00"),
        (1004, 3, 1, 3, 20240214, 2, 9492.0, "2024-02-14 13:45:00"),
        (1005, 4, 3, 4, 20240303, 1, 4294.0, "2024-03-03 16:00:00"),
        (1006, 3, 2, 2, 20240315, 2, 15142.0, "2024-03-15 20:10:00"),
    ]

    reservation_schema = StructType(
        [
            StructField("reservation_id", IntegerType(), False),
            StructField("customer_id", IntegerType(), False),
            StructField("restaurant_id", IntegerType(), False),
            StructField("time_id", IntegerType(), False),
            StructField("party_size", IntegerType(), False),
            StructField("duration_minutes", IntegerType(), False),
            StructField("table_occupied", BooleanType(), False),
            StructField("no_show", BooleanType(), False),
        ]
    )
    reservation_rows = [
        (2001, 1, 1, 20240105, 4, 90, True, False),
        (2002, 2, 2, 20240106, 2, 75, True, False),
        (2003, 3, 1, 20240214, 5, 120, True, False),
        (2004, 4, 3, 20240303, 3, 90, False, True),
        (2005, 1, 2, 20240315, 6, 110, True, False),
    ]

    return {
        "time": spark.createDataFrame(time_rows, time_schema).withColumn("full_date", F.to_date("full_date")),
        "products": spark.createDataFrame(product_rows, product_schema),
        "restaurants": spark.createDataFrame(restaurant_rows, restaurant_schema),
        "orders": spark.createDataFrame(order_rows, order_schema).withColumn(
            "order_time", F.to_timestamp("order_time_text")
        ),
        "reservations": spark.createDataFrame(reservation_rows, reservation_schema),
    }


def scale_fact_dataframes(spark: SparkSession, dataframes: dict) -> dict:
    """
    Aumenta artificialmente el volumen de hechos.

    Esto permite probar procesamiento masivo sin depender todavia del ETL real.
    SPARK_SCALE_FACTOR=1000 produce 6000 ordenes y 5000 reservas.
    """
    scale_factor = int(os.getenv("SPARK_SCALE_FACTOR", "1000"))
    batches = spark.range(0, scale_factor).withColumnRenamed("id", "batch_id")

    orders = (
        dataframes["orders"]
        .crossJoin(batches)
        .withColumn("order_id", F.col("order_id") + (F.col("batch_id") * F.lit(100000)))
        .withColumn("final_amount", F.round(F.col("final_amount") * (1 + (F.col("batch_id") % 5) * 0.01), 2))
        .drop("batch_id", "order_time_text")
    )

    reservations = (
        dataframes["reservations"]
        .crossJoin(batches)
        .withColumn("reservation_id", F.col("reservation_id") + (F.col("batch_id") * F.lit(100000)))
        .drop("batch_id")
    )

    dataframes["orders"] = orders
    dataframes["reservations"] = reservations
    return dataframes


def build_enriched_dataframes(dataframes: dict) -> dict:
    """Une hechos con dimensiones para dejar listos los datos analiticos."""
    orders_enriched = (
        dataframes["orders"]
        .join(dataframes["products"], "product_id", "inner")
        .join(dataframes["time"], "time_id", "inner")
        .join(dataframes["restaurants"], "restaurant_id", "inner")
    )

    reservations_enriched = (
        dataframes["reservations"]
        .join(dataframes["time"], "time_id", "inner")
        .join(dataframes["restaurants"], "restaurant_id", "inner")
    )

    return {
        **dataframes,
        "orders_enriched": orders_enriched.cache(),
        "reservations_enriched": reservations_enriched.cache(),
    }


def run_consumption_trends(dataframes: dict):
    """Analisis 1: tendencias de consumo usando Spark DataFrames."""
    return (
        dataframes["orders_enriched"]
        .groupBy("year", "month", "month_name", "category", "product_name")
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.sum("quantity").alias("items_sold"),
            F.round(F.sum("final_amount"), 2).alias("total_revenue"),
            F.round(F.avg("final_amount"), 2).alias("avg_ticket"),
        )
        .orderBy("year", "month", F.desc("total_revenue"))
    )


def run_peak_hours(spark: SparkSession) -> object:
    """Analisis 2: horarios pico usando SparkSQL."""
    return spark.sql(
        """
        SELECT
            day_name,
            HOUR(order_time) AS hour,
            category,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(quantity) AS items_sold,
            ROUND(SUM(final_amount), 2) AS total_revenue
        FROM orders_enriched
        GROUP BY day_name, HOUR(order_time), category
        ORDER BY total_orders DESC, total_revenue DESC
        """
    )


def run_monthly_growth(spark: SparkSession) -> object:
    """Analisis 3: crecimiento mensual usando SparkSQL y funciones ventana."""
    return spark.sql(
        """
        WITH monthly_orders AS (
            SELECT
                year,
                month,
                month_name,
                COUNT(DISTINCT order_id) AS total_orders,
                ROUND(SUM(final_amount), 2) AS total_revenue
            FROM orders_enriched
            GROUP BY year, month, month_name
        ),
        monthly_reservations AS (
            SELECT
                year,
                month,
                COUNT(DISTINCT reservation_id) AS total_reservations
            FROM reservations_enriched
            GROUP BY year, month
        ),
        monthly_joined AS (
            SELECT
                mo.year,
                mo.month,
                mo.month_name,
                mo.total_orders,
                mo.total_revenue,
                COALESCE(mr.total_reservations, 0) AS total_reservations
            FROM monthly_orders mo
            LEFT JOIN monthly_reservations mr
                ON mo.year = mr.year AND mo.month = mr.month
        )
        SELECT
            year,
            month,
            month_name,
            total_orders,
            total_revenue,
            total_reservations,
            LAG(total_revenue) OVER (ORDER BY year, month) AS previous_month_revenue,
            CASE
                WHEN LAG(total_revenue) OVER (ORDER BY year, month) IS NULL THEN NULL
                WHEN LAG(total_revenue) OVER (ORDER BY year, month) = 0 THEN NULL
                ELSE ROUND(
                    ((total_revenue - LAG(total_revenue) OVER (ORDER BY year, month))
                    / LAG(total_revenue) OVER (ORDER BY year, month)) * 100,
                    2
                )
            END AS revenue_growth_pct
        FROM monthly_joined
        ORDER BY year, month
        """
    )


def write_result(dataframe, output_name: str) -> int:
    """Guarda un resultado en CSV y retorna cuantas filas produjo."""
    output_path = OUTPUT_DIR / output_name
    row_count = dataframe.count()

    dataframe.coalesce(1).write.mode("overwrite").option("header", True).csv(str(output_path))
    return row_count


def validate_non_empty(name: str, row_count: int) -> None:
    """Falla explicitamente si un analisis requerido no produjo resultados."""
    if row_count <= 0:
        raise RuntimeError(f"Analysis '{name}' did not produce rows")


def main() -> None:
    """Orquesta la ejecucion completa del procesamiento Spark."""
    clean_output_dir()
    spark = build_spark_session()

    try:
        print("==> Building Spark DataFrames")
        dataframes = create_base_dataframes(spark)
        dataframes = scale_fact_dataframes(spark, dataframes)
        dataframes = build_enriched_dataframes(dataframes)

        dataframes["orders_enriched"].createOrReplaceTempView("orders_enriched")
        dataframes["reservations_enriched"].createOrReplaceTempView("reservations_enriched")

        input_counts = {
            "orders": dataframes["orders"].count(),
            "products": dataframes["products"].count(),
            "reservations": dataframes["reservations"].count(),
        }
        print(f"==> Input counts: {input_counts}")

        print("==> Running analysis 1: consumption trends")
        consumption_trends = run_consumption_trends(dataframes)
        consumption_trends.show(20, truncate=False)

        print("==> Running analysis 2: peak hours")
        peak_hours = run_peak_hours(spark)
        peak_hours.show(20, truncate=False)

        print("==> Running analysis 3: monthly growth")
        monthly_growth = run_monthly_growth(spark)
        monthly_growth.show(20, truncate=False)

        output_counts = {
            "consumption_trends": write_result(consumption_trends, "consumption_trends"),
            "peak_hours": write_result(peak_hours, "peak_hours"),
            "monthly_growth": write_result(monthly_growth, "monthly_growth"),
        }

        for analysis_name, row_count in output_counts.items():
            validate_non_empty(analysis_name, row_count)

        summary = {
            "status": "success",
            "spark_scale_factor": int(os.getenv("SPARK_SCALE_FACTOR", "1000")),
            "input_counts": input_counts,
            "output_counts": output_counts,
            "outputs": {
                "consumption_trends": str(OUTPUT_DIR / "consumption_trends"),
                "peak_hours": str(OUTPUT_DIR / "peak_hours"),
                "monthly_growth": str(OUTPUT_DIR / "monthly_growth"),
            },
        }
        (OUTPUT_DIR / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("==> SPARK ANALYTICS COMPLETED")
        print(json.dumps(summary, indent=2))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
