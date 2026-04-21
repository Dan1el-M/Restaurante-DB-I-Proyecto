from pydantic import BaseModel, ConfigDict

class TableBase(BaseModel):
    table_number: int
    table_status: int
    restaurant_id: int

class TableCreate(TableBase):
    pass # Hereda todo de Base

class TableUpdate(BaseModel):
    table_number: int | None = None
    table_status: int | None = None
    restaurant_id: int | None = None

class TableResponse(TableBase):
    table_id: int

    model_config = ConfigDict(from_attributes=True)