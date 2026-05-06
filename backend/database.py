import os

from dotenv import load_dotenv
from pymongo import MongoClient #conecta a mongoDB, es el cliente de mongoDB para python
from sqlalchemy import create_engine #conecta a postgreSQL, es el motor de base de datos para SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base #para que las db usen schema, es la clase base para los modelos de SQLAlchemy
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Motor activo: postgres o mongo. La API usa solo uno a la vez.
# split("#", 1)[0].strip().lower() elimina los comentarios para evitar errores del .env
DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "postgres").split("#", 1)[0].strip().lower()

# Conexion a PostgreSQL
POSTGRES_URL = os.getenv("POSTGRES_URL")

'''Si POSTGRES_URL existe, crea el engine. si no existe, engine = None.'''
engine = create_engine(POSTGRES_URL, echo=True) if POSTGRES_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
#(autocommit=False, autoflush=False, bind=engine) = configura la sesión para que no haga commit automáticamente, no haga flush automático y se conecte al engine creado.

# Clase base para todos los modelos SQLAlchemy
Base = declarative_base()

# Conexion a MongoDB
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB")
mongo_client = MongoClient(MONGO_URL) if MONGO_URL else None
mongo_db = mongo_client[MONGO_DB] if mongo_client is not None else None


def get_postgres_db():
    if SessionLocal is None:
        raise RuntimeError("POSTGRES_URL no esta configurado")

    db = SessionLocal()
    try:
        yield db #entrega la sesión al endpoint o al DAO.
    finally:
        db.close()# cierra la sesión después de usarla


def get_mongo_db():
    if mongo_db is None:
        raise RuntimeError("MONGO_URL no esta configurado")
    return mongo_db


def get_dao():
    from backend.dao import MongoDAO, PostgresDAO #no seria bueno pasar el import para arriba?

    if DATABASE_ENGINE == "mongo":
        yield MongoDAO(get_mongo_db())
        return

    elif DATABASE_ENGINE == "postgres":
        if SessionLocal is None:
            raise RuntimeError("POSTGRES_URL no esta configurado")
        db = SessionLocal()
        try:
            yield PostgresDAO(db)
        finally:
            db.close()
        return

    raise RuntimeError("DATABASE_ENGINE debe ser 'postgres' o 'mongo'")
