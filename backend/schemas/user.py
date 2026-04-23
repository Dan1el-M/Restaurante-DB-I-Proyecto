from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    user_name: str = Field(min_length=1, max_length=64)
    role_id: int = Field(gt=0)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    user_name: str | None = Field(default=None, min_length=1, max_length=64)
    role_id: int | None = Field(default=None, gt=0)


class UserResponse(UserBase):
    user_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
