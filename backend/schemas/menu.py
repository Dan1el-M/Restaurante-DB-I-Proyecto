from pydantic import BaseModel, ConfigDict

class MenuBase(BaseModel):
    dish_name: str
    price: float
    restaurant_id: int

class MenuCreate(MenuBase):
    pass # Hereda todo de Base

class MenuUpdate(BaseModel):
    dish_name: str | None = None
    price: float | None = None
    restaurant_id: int | None = None

class MenuResponse(MenuBase):
    menu_id: int

    model_config = ConfigDict(from_attributes=True)
