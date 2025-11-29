from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class Frequency(Enum):
    hour = "hour"
    day = "day"


class PeriodRange(BaseModel):
    start_date: datetime
    end_date: datetime
