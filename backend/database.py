from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexion a PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor de conexion
engine = create_engine(DATABASE_URL, echo=True)  # El echo permite ver en consola

# Fabrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Asocia a la base de datos

# Clase base para todos los modelos
Base = declarative_base() # De aqui heredan a todos los modelos

# Dependencia para FastAPI
def get_db(): # Cada vez que hay una petición
    db = SessionLocal() # Crear una sesion
    try:
        yield db # Intentar pasarla a FastAPI
    finally:
        db.close() # Cerrar sesion