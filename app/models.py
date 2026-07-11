from pydantic import BaseModel
from datetime import datetime


class Appointment(BaseModel):
    id: str
    customer_name: str
    customer_contact: str
    start_time: datetime
    notes: str = ""