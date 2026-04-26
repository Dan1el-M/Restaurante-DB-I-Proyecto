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
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar middleware de autorización
from .autentificador.keycloak_dependencies import get_current_user

# Importar routers
from backend.app.routers import auth, restaurants, reservations, menus, users

# ========== CREAR APLICACIÓN ==========

app = FastAPI(
    title="Restaurante API",
    description="API para gestión de restaurantes, reservaciones y menús",
    version="1.0.0"
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

@app.get("/ping")
def ping():
    """Health check básico"""
    return {"message": "pong"}


@app.get("/")
def root():
    """Ruta raíz"""
    return {"message": "API funcionando", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check para monitoreo"""
    return {"status": "ok"}


# ========== RUTAS DE AUTENTICACIÓN ==========

# Rutas públicas de autenticación: /auth/register y /auth/login
app.include_router(auth.router)


# ========== ROUTERS PROTEGIDOS / FUNCIONALES ==========

# Usuarios: cualquier endpoint de /users requiere token válido
app.include_router(users.router)

# Restaurantes: todos los endpoints requieren token (cliente mínimo)
# - POST, PUT, DELETE requieren rol admin dentro de restaurants.py
app.include_router(restaurants.router, dependencies=[Depends(get_current_user)])

# Menús: todos los endpoints requieren token (cliente mínimo)
# - POST, PUT, DELETE requieren rol admin dentro de menus.py
app.include_router(menus.router, dependencies=[Depends(get_current_user)])

# Reservaciones:
# Los permisos específicos se manejan dentro de reservations.py
app.include_router(reservations.router)


# ========== PUERTO ==========

if __name__ == "__main__":
    
    # Puerto y host configurables por variables de entorno
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    
    print(f"🚀 Servidor corriendo en {host}:{port}")
    
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=True
    )