import os
import socket

from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/instance")
def get_instance():
    return {
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "container": socket.gethostname(),
    }
