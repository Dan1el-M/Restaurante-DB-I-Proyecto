"""Router de menus."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO, DAOConflictError
from backend.database import get_dao
from backend.schemas.menu import MenuCreate, MenuResponse, MenuUpdate
from backend.utils.auth import has_admin_role

router = APIRouter(prefix="/menus", tags=["Menus"])


@router.get("/", response_model=list[MenuResponse])
def list_menus(token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    """Lista todos los menus."""
    return dao.list_menus()


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(menu_id: int, token_payload=Depends(get_current_user), dao: BaseDAO = Depends(get_dao)):
    """Obtiene un menu por su ID."""
    menu = dao.get_menu(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu no encontrado",
        )
    return menu


@router.post("/", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    payload: MenuCreate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Crea un nuevo menu."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear menus",
        )

    if not dao.get_restaurant(payload.restaurant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El restaurante no existe")

    try:
        return dao.create_menu(payload.model_dump())
    except DAOConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato con ese nombre en este restaurante",
        )


@router.put("/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Actualiza parcialmente un menu existente."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar menus",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar",
        )

    if "restaurant_id" in data and not dao.get_restaurant(data["restaurant_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El restaurante no existe")

    try:
        menu = dao.update_menu(menu_id, data)
    except DAOConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato con ese nombre en este restaurante",
        )

    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu no encontrado",
        )
    return menu


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: int,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Elimina un menu."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar menus",
        )

    if not dao.delete_menu(menu_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu no encontrado",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
