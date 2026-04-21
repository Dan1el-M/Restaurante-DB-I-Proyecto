from pydantic import BaseModel, ConfigDict, Field

class RestaurantBase(BaseModel):
    restaurant_name: str
    admin_id: int
    restaurant_status: int

class RestaurantCreate(RestaurantBase):
    pass # Hereda todo de Base

class RestaurantUpdate(BaseModel):
    restaurant_name: str | None = Field(default=None, min_length=1, max_length=64)
    admin_id: int | None = None
    restaurant_status: int | None = None

# Respuesta (lo que devuelve la API)
class RestaurantResponse(RestaurantBase):
    restaurant_id: int

    model_config = ConfigDict(from_attributes=True)
