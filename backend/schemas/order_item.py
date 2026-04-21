from pydantic import BaseModel, ConfigDict

class OrderItemBase(BaseModel):
    order_id: int
    menu_id: int
    quantity: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass # Hereda todo de Base

class OrderItemUpdate(BaseModel):
    order_id: int | None = None
    menu_id: int | None = None
    quantity: int | None = None
    price: float | None = None

class OrderItemResponse(OrderItemBase):
    order_item_id: int

    model_config = ConfigDict(from_attributes=True)
