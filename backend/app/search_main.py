import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import debug, search

ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")

app = FastAPI(
    title="Restaurante Search",
    description="Microservicio de búsqueda",
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

@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(search.router)
app.include_router(debug.router)
