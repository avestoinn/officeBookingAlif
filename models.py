from pydantic import BaseModel
from pydantic import validator
import datetime


class Room(BaseModel):
    id: int
    name: str


class Appointment(BaseModel):
    id: int
    begin_dt: datetime.datetime
    end_dt: datetime.datetime
    room_id: int

    @validator('begin_dt')
    def begin_dt_validate(cls, v):
        val = datetime.datetime.strptime(v, '%d.%m.%Y %H:%M')
        return val

    @validator('end_dt')
    def end_dt_validate(cls, v):
        val = datetime.datetime.strptime(v, '%d.%m.%Y %H:%M')
        return val
