from pydantic import BaseModel, ConfigDict, Field


class TableBase(BaseModel):
    table_number: int = Field(gt=0)
    table_status: int = Field(ge=0, le=2)
    restaurant_id: int = Field(gt=0)


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    table_number: int | None = Field(default=None, gt=0)
    table_status: int | None = Field(default=None, ge=0, le=2)
    restaurant_id: int | None = Field(default=None, gt=0)


class TableResponse(TableBase):
    table_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
