from pydantic import BaseModel, ConfigDict

class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    pass # Hereda todo de Base

class RoleUpdate(BaseModel):
    role_name: str | None = None

class RoleResponse(RoleBase):
    role_id: int

    model_config = ConfigDict(from_attributes=True)
