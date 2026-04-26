"""Router de mesas."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.utils.auth import has_admin_role
from backend.database import get_db
from backend.models.tables import Table
from backend.models.restaurants import Restaurant
from backend.schemas.table import TableCreate, TableResponse, TableUpdate

router = APIRouter(prefix="/tables", tags=["Mesas"])


@router.get("/", response_model=list[TableResponse])
def list_tables(token_payload=Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Lista todas las mesas."""
    return db.query(Table).all()


@router.get("/{table_id}", response_model=TableResponse)
def get_table(table_id: int, token_payload=Depends(get_current_user),
              db: Session = Depends(get_db)):
    """Obtiene una mesa por su ID."""
    table = db.query(Table).filter(Table.table_id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )
    return table


@router.post(
    "/",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_table(
    payload: TableCreate,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea una nueva mesa. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear mesas",
        )
    
    # Validar que el restaurante existe
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El restaurante no existe",
        )
    
    table = Table(**payload.model_dump())
    db.add(table)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con ese número en este restaurante",
        )

    db.refresh(table)
    return table


@router.put(
    "/{table_id}",
    response_model=TableResponse,
)
def update_table(
    table_id: int,
    payload: TableUpdate,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente una mesa. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar mesas",
        )
    
    table = db.query(Table).filter(Table.table_id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar",
        )

    # Validar que el restaurante existe si se intenta cambiar
    if "restaurant_id" in data:
        restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == data["restaurant_id"]).first()
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El restaurante no existe",
            )

    for field, value in data.items():
        setattr(table, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con ese número en este restaurante",
        )

    db.refresh(table)
    return table


@router.delete(
    "/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_table(
    table_id: int,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Elimina una mesa por su ID. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar mesas",
        )
    
    table = db.query(Table).filter(Table.table_id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    db.delete(table)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
