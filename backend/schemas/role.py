from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    role_name: str = Field(min_length=1, max_length=64)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    role_name: str | None = Field(default=None, min_length=1, max_length=64)


class RoleResponse(RoleBase):
    role_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
