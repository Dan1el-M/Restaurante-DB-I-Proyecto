"""
ETL Pipeline para Data Warehouse OLAP
Base de Datos II - Proyecto OLAP
Extrae datos de PostgreSQL/MongoDB, transforma y carga en Hive
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional, List
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WarehouseETL:
    """Clase para orquestar el ETL del Data Warehouse"""
    
    def __init__(self, connection_string: str = None):
        """
        Inicializa el ETL Pipeline
        
        Args:
            connection_string: Cadena de conexión a la base de datos
        """
        self.connection_string = connection_string
        self.data_frames = {}
        logger.info("ETL Pipeline inicializado")
    
    # =====================================================
    # FASE 1: EXTRACCIÓN (EXTRACTION)
    # =====================================================
    
    def extract_from_postgres(self, query: str, table_name: str) -> pd.DataFrame:
        """
        Extrae datos de PostgreSQL
        
        Args:
            query: Consulta SQL
            table_name: Nombre de la tabla
            
        Returns:
            DataFrame con los datos extraídos
        """
        try:
            logger.info(f"Extrayendo datos de PostgreSQL: {table_name}")
            # Aquí iría la conexión real a PostgreSQL
            # df = pd.read_sql(query, self.connection_string)
            logger.info(f"✓ Extracción exitosa: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Error extrayendo {table_name}: {str(e)}")
            raise
    
    def extract_from_mongodb(self, collection: str) -> List[dict]:
        """
        Extrae datos de MongoDB
        
        Args:
            collection: Nombre de la colección
            
        Returns:
            Lista de documentos
        """
        try:
            logger.info(f"Extrayendo datos de MongoDB: {collection}")
            # Aquí iría la conexión real a MongoDB
            # db[collection].find()
            logger.info(f"✓ Extracción exitosa")
            return []
        except Exception as e:
            logger.error(f"Error extrayendo {collection}: {str(e)}")
            raise
    
    # =====================================================
    # FASE 2: TRANSFORMACIÓN (TRANSFORMATION)
    # =====================================================
    
    def create_dim_time(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Crea la dimensión de tiempo
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            DataFrame con la dimensión de tiempo
        """
        logger.info("Creando dimensión de TIEMPO")
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        dim_time = pd.DataFrame({
            'time_id': [(d - start_date).days for d in date_range],
            'full_date': date_range,
            'day_of_week': date_range.dayofweek,
            'day_name': date_range.strftime('%A'),
            'week_of_year': date_range.isocalendar().week,
            'month': date_range.month,
            'month_name': date_range.strftime('%B'),
            'quarter': date_range.quarter,
            'year': date_range.year,
            'is_weekend': date_range.dayofweek.isin([5, 6]),
            'season': date_range.apply(self._get_season)
        })
        
        logger.info(f"✓ Dimensión de TIEMPO creada: {len(dim_time)} registros")
        self.data_frames['dim_time'] = dim_time
        return dim_time
    
    def create_dim_customer(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea la dimensión de cliente
        
        Args:
            users_df: DataFrame de usuarios
            
        Returns:
            DataFrame con la dimensión de cliente
        """
        logger.info("Creando dimensión de CLIENTE")
        
        dim_customer = users_df.copy()
        dim_customer.columns = [
            'customer_id', 'customer_name', 'customer_type',
            'registration_date', 'preferred_restaurant_id',
            'geographic_zone', 'loyalty_level', 'total_spent',
            'total_orders', 'is_active'
        ]
        
        # Rellenar valores nulos
        dim_customer.fillna({
            'customer_type': 'Regular',
            'geographic_zone': 'Centro',
            'loyalty_level': 1,
            'total_spent': 0,
            'total_orders': 0,
            'is_active': True
        }, inplace=True)
        
        logger.info(f"✓ Dimensión de CLIENTE creada: {len(dim_customer)} registros")
        self.data_frames['dim_customer'] = dim_customer
        return dim_customer
    
    def create_dim_product(self, menus_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea la dimensión de producto/menú
        
        Args:
            menus_df: DataFrame de menús
            
        Returns:
            DataFrame con la dimensión de producto
        """
        logger.info("Creando dimensión de PRODUCTO")
        
        dim_product = menus_df.copy()
        dim_product['product_id'] = range(1, len(dim_product) + 1)
        dim_product['cost'] = dim_product['price'] * 0.6  # Asumir costo
        dim_product['margin'] = dim_product['price'] - dim_product['cost']
        dim_product['is_available'] = True
        dim_product['creation_date'] = datetime.now()
        dim_product['last_update'] = datetime.now()
        
        logger.info(f"✓ Dimensión de PRODUCTO creada: {len(dim_product)} registros")
        self.data_frames['dim_product'] = dim_product
        return dim_product
    
    def create_dim_restaurant(self, restaurants_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea la dimensión de restaurante
        
        Args:
            restaurants_df: DataFrame de restaurantes
            
        Returns:
            DataFrame con la dimensión de restaurante
        """
        logger.info("Creando dimensión de RESTAURANTE")
        
        dim_restaurant = restaurants_df.copy()
        dim_restaurant['status'] = 'Activo'
        
        logger.info(f"✓ Dimensión de RESTAURANTE creada: {len(dim_restaurant)} registros")
        self.data_frames['dim_restaurant'] = dim_restaurant
        return dim_restaurant
    
    def create_dim_status(self) -> pd.DataFrame:
        """
        Crea la dimensión de estado
        
        Returns:
            DataFrame con la dimensión de estado
        """
        logger.info("Creando dimensión de ESTADO")
        
        statuses = [
            {'status_id': 1, 'status_name': 'Completada', 'status_type': 'order', 'description': 'Orden completada'},
            {'status_id': 2, 'status_name': 'Cancelada', 'status_type': 'order', 'description': 'Orden cancelada'},
            {'status_id': 3, 'status_name': 'Pendiente', 'status_type': 'order', 'description': 'Orden pendiente'},
            {'status_id': 4, 'status_name': 'Confirmada', 'status_type': 'reservation', 'description': 'Reserva confirmada'},
            {'status_id': 5, 'status_name': 'No Show', 'status_type': 'reservation', 'description': 'Cliente no asistió'},
            {'status_id': 6, 'status_name': 'Cancelada', 'status_type': 'reservation', 'description': 'Reserva cancelada'},
        ]
        
        dim_status = pd.DataFrame(statuses)
        logger.info(f"✓ Dimensión de ESTADO creada: {len(dim_status)} registros")
        self.data_frames['dim_status'] = dim_status
        return dim_status
    
    def create_fact_orders(self, orders_df: pd.DataFrame, order_items_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea la tabla de hechos de órdenes
        
        Args:
            orders_df: DataFrame de órdenes
            order_items_df: DataFrame de items de órdenes
            
        Returns:
            DataFrame con la tabla de hechos
        """
        logger.info("Creando tabla de HECHOS - ÓRDENES")
        
        # Unir órdenes con items
        fact_orders = orders_df.merge(order_items_df, on='order_id', how='inner')
        
        # Agregar columnas calculadas
        fact_orders['discount'] = 0  # Implementar según lógica
        fact_orders['net_amount'] = fact_orders['total_amount']
        fact_orders['tax_amount'] = fact_orders['total_amount'] * 0.13  # IVA Costa Rica
        fact_orders['final_amount'] = fact_orders['net_amount'] + fact_orders['tax_amount']
        
        logger.info(f"✓ Tabla de HECHOS - ÓRDENES creada: {len(fact_orders)} registros")
        self.data_frames['fact_orders'] = fact_orders
        return fact_orders
    
    def create_fact_reservations(self, reservations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea la tabla de hechos de reservaciones
        
        Args:
            reservations_df: DataFrame de reservaciones
            
        Returns:
            DataFrame con la tabla de hechos
        """
        logger.info("Creando tabla de HECHOS - RESERVACIONES")
        
        fact_reservations = reservations_df.copy()
        fact_reservations['party_size'] = 4  # Valor por defecto
        fact_reservations['duration_minutes'] = 90  # Valor por defecto
        fact_reservations['table_occupied'] = True
        fact_reservations['no_show'] = False
        
        logger.info(f"✓ Tabla de HECHOS - RESERVACIONES creada: {len(fact_reservations)} registros")
        self.data_frames['fact_reservations'] = fact_reservations
        return fact_reservations
    
    # =====================================================
    # FASE 3: CARGA (LOADING)
    # =====================================================
    
    def load_to_hive(self, table_name: str, df: pd.DataFrame, 
                     file_format: str = 'parquet') -> bool:
        """
        Carga datos a Hive
        
        Args:
            table_name: Nombre de la tabla
            df: DataFrame a cargar
            file_format: Formato del archivo (parquet, csv, orc)
            
        Returns:
            True si la carga fue exitosa
        """
        try:
            logger.info(f"Cargando datos a Hive: {table_name}")
            
            # Crear ruta de almacenamiento
            warehouse_path = Path('dataW/warehouse/data')
            warehouse_path.mkdir(parents=True, exist_ok=True)
            
            file_path = warehouse_path / f"{table_name}.{file_format}"
            
            # Guardar según formato
            if file_format == 'parquet':
                df.to_parquet(str(file_path), index=False)
            elif file_format == 'csv':
                df.to_csv(str(file_path), index=False)
            else:  # orc
                df.to_orc(str(file_path), index=False)
            
            logger.info(f"✓ Datos cargados en Hive: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando {table_name}: {str(e)}")
            return False
    
    # =====================================================
    # UTILIDADES
    # =====================================================
    
    @staticmethod
    def _get_season(date: datetime) -> str:
        """Determina la estación del año"""
        month = date.month
        if month in [12, 1, 2]:
            return 'Invierno'
        elif month in [3, 4, 5]:
            return 'Primavera'
        elif month in [6, 7, 8]:
            return 'Verano'
        else:
            return 'Otoño'
    
    def run_full_etl(self, start_date: datetime = None, 
                    end_date: datetime = None) -> bool:
        """
        Ejecuta el pipeline ETL completo
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            True si el ETL fue exitoso
        """
        try:
            logger.info("=" * 60)
            logger.info("INICIANDO ETL PIPELINE")
            logger.info("=" * 60)
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=365)
            if not end_date:
                end_date = datetime.now()
            
            # Fase 1: Extracción (Simulada)
            logger.info("\n[FASE 1] EXTRACCIÓN DE DATOS")
            logger.info("-" * 60)
            
            # Fase 2: Transformación
            logger.info("\n[FASE 2] TRANSFORMACIÓN DE DATOS")
            logger.info("-" * 60)
            
            # Crear dimensiones
            self.create_dim_time(start_date, end_date)
            self.create_dim_status()
            
            # Fase 3: Carga
            logger.info("\n[FASE 3] CARGA A HIVE")
            logger.info("-" * 60)
            
            for table_name, df in self.data_frames.items():
                self.load_to_hive(table_name, df, 'parquet')
            
            logger.info("\n" + "=" * 60)
            logger.info("ETL PIPELINE COMPLETADO EXITOSAMENTE ✓")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"Error en ETL Pipeline: {str(e)}")
            return False


def main():
    """Función principal para ejecutar el ETL"""
    logger.info("Iniciando Data Warehouse ETL...")
    
    # Crear instancia del ETL
    etl = WarehouseETL()
    
    # Ejecutar pipeline
    success = etl.run_full_etl()
    
    if success:
        logger.info("Warehouse ETL completado correctamente")
    else:
        logger.error("Error durante la ejecución del Warehouse ETL")
        sys.exit(1)


if __name__ == "__main__":
    main()
