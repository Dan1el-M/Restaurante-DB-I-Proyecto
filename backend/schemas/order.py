from pydantic import BaseModel, ConfigDict, Field


class OrderBase(BaseModel):
    table_id: int | None = Field(default=None, gt=0)
    client_id: int = Field(gt=0)
    order_type: str = Field(min_length=1, max_length=64)
    restaurant_id: int = Field(gt=0)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    table_id: int | None = Field(default=None, gt=0)
    client_id: int | None = Field(default=None, gt=0)
    order_type: str | None = Field(default=None, min_length=1, max_length=64)
    restaurant_id: int | None = Field(default=None, gt=0)


class OrderResponse(OrderBase):
    order_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
