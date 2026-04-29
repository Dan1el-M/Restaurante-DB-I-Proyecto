"""Router de menús."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.autentificador.keycloak_dependencies import get_current_user
from backend.utils.auth import has_admin_role
from backend.database import get_db
from backend.models.menus import Menu
from backend.schemas.menu import MenuCreate, MenuResponse, MenuUpdate

router = APIRouter(prefix="/menus", tags=["Menús"])


@router.get("/", response_model=list[MenuResponse])
def list_menus(token_payload=Depends(get_current_user),
               db: Session = Depends(get_db)):
    """Lista todos los menús."""
    return db.query(Menu).all()


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(menu_id: int, token_payload=Depends(get_current_user),
             db: Session = Depends(get_db)):
    """Obtiene un menú por su ID."""
    menu = db.query(Menu).filter(Menu.menu_id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado",
        )
    return menu


@router.post(
    "/",
    response_model=MenuResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu(
    payload: MenuCreate,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un nuevo menú."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear menús",
        )
    
    menu = Menu(**payload.model_dump())
    db.add(menu)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato con ese nombre en este restaurante",
        )

    db.refresh(menu)
    return menu


@router.put(
    "/{menu_id}",
    response_model=MenuResponse,
)
def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente un menú existente."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar menús",
        )
    
    menu = db.query(Menu).filter(Menu.menu_id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar",
        )

    for field, value in data.items():
        setattr(menu, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato con ese nombre en este restaurante",
        )

    db.refresh(menu)
    return menu


@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu(
    menu_id: int,
    token_payload=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Elimina un menú por su ID."""
    if not has_admin_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar menús",
        )
    
    menu = db.query(Menu).filter(Menu.menu_id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado",
        )

    db.delete(menu)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
