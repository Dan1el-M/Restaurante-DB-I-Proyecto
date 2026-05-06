# backend/app/main.py
"""
Servidor API para gestión de restaurantes con Keycloak
Estructura:
- Rutas públicas (ping, health)
- Rutas de autenticación (registro, login)
- Rutas protegidas por rol dentro de cada router
"""

import os
import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar routers
from backend.app.routers import auth, menus, orders, reservations, restaurants, search, tables, users

# ========== CREAR APLICACIÓN ==========

API_PREFIX = "/api"
SEARCH_PREFIX = "/search"
SERVICE_MODE = os.getenv("SERVICE_MODE", "api").lower()
DOCS_PREFIX = SEARCH_PREFIX if SERVICE_MODE == "search" else API_PREFIX

app = FastAPI(
    title="Restaurante API",
    description="API para gestión de restaurantes, reservaciones y menús",
    version="1.0.0",
    docs_url=f"{DOCS_PREFIX}/docs",
    redoc_url=f"{DOCS_PREFIX}/redoc",
    openapi_url=f"{DOCS_PREFIX}/openapi.json",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== RUTAS PÚBLICAS ==========

# Estas podemos eliminarlas después; solo las dejo para pruebas de conexión

api_public_router = APIRouter(prefix=API_PREFIX, tags=["Sistema"])

@api_public_router.get("/ping")
def ping():
    """Health check básico"""
    return {"message": "pong"}


if SERVICE_MODE in ("api", "all"):
    app.include_router(api_public_router)

    # ========== RUTAS DE AUTENTICACIÓN ==========

    # Rutas públicas de autenticación: /api/auth/register y /api/auth/login
    app.include_router(auth.router, prefix=API_PREFIX)


    # ========== ROUTERS PROTEGIDOS / FUNCIONALES ==========

    # Usuarios: cualquier endpoint de /api/users requiere token válido
    app.include_router(users.router, prefix=API_PREFIX)

    # Restaurantes: todos los endpoints requieren token (cliente mínimo)
    # - POST, PUT, DELETE requieren rol admin dentro de restaurants.py
    app.include_router(restaurants.router, prefix=API_PREFIX)

    # Menús: todos los endpoints requieren token (cliente mínimo)
    # - POST, PUT, DELETE requieren rol admin dentro de menus.py
    app.include_router(menus.router, prefix=API_PREFIX)

    # Reservaciones: todos los endpoints requieren token válido (cliente mínimo)
    # - No hay restricción de rol, solo requiere estar autenticado
    app.include_router(reservations.router, prefix=API_PREFIX)

    # Pedidos: todos los endpoints requieren token válido (cliente mínimo)
    # - No hay restricción de rol, solo requiere estar autenticado
    app.include_router(orders.router, prefix=API_PREFIX)

    # Mesas: todos los endpoints requieren token (cliente mínimo)
    # - POST, PUT, DELETE requieren rol admin dentro de tables.py
    app.include_router(tables.router, prefix=API_PREFIX)

if SERVICE_MODE in ("search", "all"):
    # busqueda: todos los endpoints requieren token (cliente mínimo)
    # GET /search/products?q=texto — Busqueda textual en productos.
    # GET /search/products/category/:categoria — Filtrar por categoria.
    # POST /search/reindex — Reindexar productos manualmente.
    app.include_router(search.router)

# ========== PUERTO ==========

if __name__ == "__main__":
    
    # Puerto y host configurables por variables de entorno
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    print(f"🚀 Servidor corriendo en {host}:{port}")
    
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=True
    )
