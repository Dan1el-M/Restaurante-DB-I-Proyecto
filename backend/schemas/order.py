from pydantic import BaseModel, ConfigDict

class OrderBase(BaseModel):
    table_id: int | None = None
    client_id: int
    order_type: str
    restaurant_id: int

class OrderCreate(OrderBase):
    pass # Hereda todo de Base

class OrderUpdate(BaseModel):
    table_id: int | None = None
    client_id: int | None = None
    order_type: str | None = None
    restaurant_id: int | None = None

# Respuesta (lo que devuelve la API)
class OrderResponse(OrderBase):
    order_id: int

    model_config = ConfigDict(from_attributes=True)
