"""Router de reservaciones."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.database import get_db
from backend.models.reservations import Reservation
from backend.models.tables import Table
from backend.models.users import User
from backend.schemas.reservation import ReservationCreate, ReservationResponse

router = APIRouter(prefix="/reservations", tags=["Reservaciones"])


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, token_payload=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """Crear una nueva reserva."""

    # Validar que la mesa existe
    table = db.query(Table).filter(Table.table_id == payload.table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La mesa no existe"
        )
    
    # Validar que el cliente existe
    client = db.query(User).filter(User.user_id == payload.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no existe",
        )

    reservation = Reservation(**payload.model_dump())
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: int, token_payload=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """Cancelar (eliminar) una reserva por su ID."""
    reservation = db.query(Reservation).filter(Reservation.reservation_id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservación no encontrada",
        )

    db.delete(reservation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)