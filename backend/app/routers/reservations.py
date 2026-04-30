"""Router de reservaciones."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO
from backend.database import get_dao
from backend.schemas.reservation import ReservationCreate, ReservationResponse

router = APIRouter(prefix="/reservations", tags=["Reservaciones"])


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Crear una nueva reserva."""
    if not dao.get_table(payload.table_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mesa no existe")

    if not dao.get_user(payload.client_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no existe")

    return dao.create_reservation(payload.model_dump())


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: int,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Cancelar una reserva por su ID."""
    if not dao.delete_reservation(reservation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservacion no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
