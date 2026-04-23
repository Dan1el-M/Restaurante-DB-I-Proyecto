from pydantic import BaseModel, ConfigDict, Field


class MenuBase(BaseModel):
    dish_name: str = Field(min_length=1, max_length=64)
    price: float = Field(gt=0)
    restaurant_id: int = Field(gt=0)


class MenuCreate(MenuBase):
    pass


class MenuUpdate(BaseModel):
    dish_name: str | None = Field(default=None, min_length=1, max_length=64)
    price: float | None = Field(default=None, gt=0)
    restaurant_id: int | None = Field(default=None, gt=0)


class MenuResponse(MenuBase):
    menu_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
