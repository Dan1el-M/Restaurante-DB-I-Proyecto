import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import auth, debug, graph, menus, orders, reservations, restaurants, tables, users

ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")

app = FastAPI(
    title="Restaurante API",
    description="API para gestión de restaurantes, reservaciones y menús",
    version="1.0.0",
    root_path=ROOT_PATH,
    root_path_in_servers=False,
    servers=[{"url": ROOT_PATH}] if ROOT_PATH else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/")
def root():
    return {"message": "API funcionando", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(restaurants.router)
app.include_router(menus.router)
app.include_router(reservations.router)
app.include_router(orders.router)
app.include_router(tables.router)
app.include_router(graph.router)

app.include_router(debug.router)
