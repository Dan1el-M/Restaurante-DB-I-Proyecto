"""Router de restaurantes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.dao import BaseDAO
from backend.utils.auth import has_admin_role
from backend.database import get_dao
from backend.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["Restaurantes"])


@router.get("/", response_model=list[RestaurantResponse])
def list_restaurants(token_payload=Depends(get_current_user),
                     dao: BaseDAO = Depends(get_dao)):
    """Lista todos los restaurantes."""
    return dao.list_restaurants()


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: int, token_payload=Depends(get_current_user),
                   dao: BaseDAO = Depends(get_dao)):
    """Obtiene un restaurante por su ID."""
    restaurant = dao.get_restaurant(restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )
    return restaurant


@router.post(
    "/",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    payload: RestaurantCreate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Crea un restaurante."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear restaurantes",
        )

    if not dao.get_user(payload.admin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El administrador no existe",
        )
    
    return dao.create_restaurant(payload.model_dump())


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Actualiza parcialmente un restaurante existente."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar restaurantes",
        )
    
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar",
        )

    if "admin_id" in data and not dao.get_user(data["admin_id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El administrador no existe",
        )

    restaurant = dao.update_restaurant(restaurant_id, data)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )
    return restaurant


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_restaurant(
    restaurant_id: int,
    token_payload=Depends(get_current_user),
    dao: BaseDAO = Depends(get_dao),
):
    """Elimina un restaurante por su ID."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar restaurantes",
        )
    
    if not dao.delete_restaurant(restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
