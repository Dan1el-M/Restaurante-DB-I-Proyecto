from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ReservationBase(BaseModel):
    table_id: int
    client_id: int
    reservation_date: datetime
    reservation_status: int

class ReservationCreate(ReservationBase):
    pass # Hereda todo de Base

class ReservationUpdate(BaseModel):
    table_id: int | None = None
    client_id: int | None = None
    reservation_date: datetime | None = None
    reservation_status: int | None = None

class ReservationResponse(ReservationBase):
    reservation_id: int

    model_config = ConfigDict(from_attributes=True)
