"""Router de pedidos."""

from backend.models.tables import Table
from backend.models.users import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.database import get_db
from backend.models.orders import Order
from backend.schemas.order import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, token_payload=Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """Realizar un pedido."""

    # Validar que la mesa existe (si se proporciona)
    if payload.table_id:
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
    
    # El restaurant_id y los demás campos vienen en el payload
    order = Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, token_payload=Depends(get_current_user),
              db: Session = Depends(get_db)):
    """Obtener detalles de un pedido por su ID."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado",
        )

    return order