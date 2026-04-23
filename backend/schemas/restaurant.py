from pydantic import BaseModel, ConfigDict, Field


class RestaurantBase(BaseModel):
    restaurant_name: str = Field(min_length=1, max_length=64)
    admin_id: int = Field(gt=0)
    restaurant_status: int = Field(ge=0)


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    restaurant_name: str | None = Field(default=None, min_length=1, max_length=64)
    admin_id: int | None = Field(default=None, gt=0)
    restaurant_status: int | None = Field(default=None, ge=0)


class RestaurantResponse(RestaurantBase):
    restaurant_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
