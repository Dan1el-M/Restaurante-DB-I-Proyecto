from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReservationBase(BaseModel):
    table_id: int = Field(gt=0)
    client_id: int = Field(gt=0)
    reservation_date: datetime
    reservation_status: int = Field(ge=0)


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    table_id: int | None = Field(default=None, gt=0)
    client_id: int | None = Field(default=None, gt=0)
    reservation_date: datetime | None = None
    reservation_status: int | None = Field(default=None, ge=0)


class ReservationResponse(ReservationBase):
    reservation_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)
