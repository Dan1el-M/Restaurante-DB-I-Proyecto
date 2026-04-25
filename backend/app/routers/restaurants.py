"""Router de restaurantes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.autentificador.keycloak_dependencies import require_role
from backend.database import get_db
from backend.models.restaurants import Restaurant
from backend.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["Restaurantes"])


@router.get("/", response_model=list[RestaurantResponse])
def list_restaurants(db: Session = Depends(get_db)):
    """Lista todos los restaurantes."""
    return db.query(Restaurant).all()


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Obtiene un restaurante por su ID."""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
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
    dependencies=[Depends(require_role("admin"))],
)
def create_restaurant(payload: RestaurantCreate, db: Session = Depends(get_db)):
    """Crea un restaurante."""
    restaurant = Restaurant(**payload.model_dump())
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    dependencies=[Depends(require_role("admin"))],
)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente un restaurante existente."""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar",
        )

    for field, value in data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Elimina un restaurante por su ID."""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )

    db.delete(restaurant)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)