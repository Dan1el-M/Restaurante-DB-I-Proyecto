# backend/app/main.py
from fastapi import Depends, FastAPI

from backend.app.autentificador.keycloak_dependencies import require_role
from backend.app.autentificador.keycloak_dependencies import get_current_user, require_role

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API funcionando"}

#ambos usuarios se estan haciendo manuelmente por el momento

#ruta para el admin
@app.get("/admin")
def admin_route(user=Depends(require_role("admin"))):
    return {"message": "solo admin", "user": user.get("preferred_username")}

#ruta para el client
@app.get("/client")
def client_route(user=Depends(require_role("client"))):
    return {"message": "solo client", "user": user.get("preferred_username")}

#rutas temporales para preubas
@app.get("/test-validate")
def test_validate(payload=Depends(get_current_user)):
    return payload

@app.get("/test-client")
def test_client(payload=Depends(require_role("client"))):
    return {"message": "ok", "payload": payload}