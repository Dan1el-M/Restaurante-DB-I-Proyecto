"""Router de pedidos."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO
from backend.database import get_dao
from backend.schemas.order import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Realizar un pedido."""
    if payload.table_id and not dao.get_table(payload.table_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mesa no existe")

    if not dao.get_user(payload.client_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no existe")

    if not dao.get_restaurant(payload.restaurant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El restaurante no existe")

    return dao.create_order(payload.model_dump())


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    """Obtener detalles de un pedido por su ID."""
    order = dao.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return order
