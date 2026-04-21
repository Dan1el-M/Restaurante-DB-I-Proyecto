# backend/app/main.py
"""
Servidor API para gestión de restaurantes con Keycloak
Estructura:
- Rutas públicas (ping, health)
- Rutas de autenticación (registro, login)
- Rutas protegidas por rol (client, admin)
"""

import os
from fastapi import Depends, FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar middleware de autorización
from backend.app.autentificador.keycloak_dependencies import get_current_user, require_role

# Importar routers
from backend.app.routers import restaurants, reservations, menus, users

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

@app.post("/auth/register")
def register():
    """Registro de usuarios"""
    # TODO: Implementar registro
    pass

@app.post("/auth/login")
def login():
    """Login de usuarios"""
    # TODO: Implementar login
    pass

# ========== ROUTERS PROTEGIDOS POR ROL ==========

# --------- CLIENT ROUTES ---------
# Rutas que requieren rol 'client'
client_routes = APIRouter(dependencies=[Depends(require_role("client"))])

client_routes.include_router(restaurants.router, tags=["Client - Restaurants"])
client_routes.include_router(reservations.router, tags=["Client - Reservations"])
client_routes.include_router(menus.router, tags=["Client - Menus"])

app.include_router(client_routes)

# --------- ADMIN ROUTES ---------
# Rutas que requieren rol 'admin'
admin_routes = APIRouter(dependencies=[Depends(require_role("admin"))])

admin_routes.include_router(users.router, tags=["Admin - Users"])

app.include_router(admin_routes)

# ========== PUERTO ==========

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    
    print(f"🚀 Servidor corriendo en {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
