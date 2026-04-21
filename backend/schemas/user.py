from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    user_name: str
    role_id: int

class UserCreate(UserBase):
    pass # Hereda todo

class UserUpdate(BaseModel):
    user_name: str | None = None
    role_id: int | None = None

# Lo que devuelve el API
class UserResponse(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)