from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
    order_id: int = Field(gt=0)
    menu_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    order_id: int | None = Field(default=None, gt=0)
    menu_id: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)


class OrderItemResponse(OrderItemBase):
    order_item_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
