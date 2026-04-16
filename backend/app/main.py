# backend/app/main.py
from fastapi import Depends, FastAPI

from app.autentificador.keycloak_dependencies import require_role

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API funcionando"}


@app.get("/admin")
def admin_route(user=Depends(require_role("admin"))):
    # Protected endpoint: only users with the admin role can access it.
    return {"message": "solo admin", "user": user.get("preferred_username")}


@app.get("/client")
def client_route(user=Depends(require_role("client"))):
    # Protected endpoint: only users with the client role can access it.
    return {"message": "solo client", "user": user.get("preferred_username")}