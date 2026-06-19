"""Router de mesas."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO, DAOConflictError
from backend.database import get_dao
from backend.schemas.table import TableCreate, TableResponse, TableUpdate
from backend.utils.auth import has_admin_role

router = APIRouter(prefix="/tables", tags=["Mesas"])


@router.get("/", response_model=list[TableResponse])
def list_tables(token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    """Lista todas las mesas."""
    return dao.list_tables()


@router.get("/{table_id}", response_model=TableResponse)
def get_table(table_id: int, token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    """Obtiene una mesa por su ID."""
    table = dao.get_table(table_id)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")
    return table


@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Crea una nueva mesa. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear mesas",
        )

    if not dao.get_restaurant(payload.restaurant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El restaurante no existe")

    try:
        return dao.create_table(payload.model_dump())
    except DAOConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con ese numero en este restaurante",
        )


@router.put("/{table_id}", response_model=TableResponse)
def update_table(
    table_id: int,
    payload: TableUpdate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Actualiza parcialmente una mesa. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar mesas",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se enviaron campos para actualizar")

    if "restaurant_id" in data and not dao.get_restaurant(data["restaurant_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El restaurante no existe")

    try:
        table = dao.update_table(table_id, data)
    except DAOConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con ese numero en este restaurante",
        )

    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")
    return table


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: int,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Elimina una mesa por su ID. Solo admin."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar mesas",
        )

    if not dao.delete_table(table_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
