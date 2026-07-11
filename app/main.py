import uuid
from fastapi import FastAPI, HTTPException
from datetime import datetime, date
from pydantic import BaseModel
from app.models import Appointment
from app.storage import appointments_db
from app.ai_agent import understand_message, resolve_date
from app.booking_logic import get_available_slots, validate_booking_time, WORK_START_HOUR, WORK_END_HOUR

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Appointment Booking Agent is running"}


@app.get("/appointments")
def list_appointments():
    return list(appointments_db.values())


@app.get("/available-slots")
def available_slots(day: date):
    return {"day": str(day), "available_slots": get_available_slots(day)}


@app.post("/appointments")
def create_appointment(appointment: Appointment):
    error = validate_booking_time(appointment.start_time)
    if error:
        code = 409 if "already booked" in error else 400
        raise HTTPException(status_code=code, detail=error)

    appointments_db[appointment.id] = appointment
    return appointment


@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: str):
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    del appointments_db[appointment_id]
    return {"message": f"Appointment {appointment_id} cancelled."}


class ChatMessage(BaseModel):
    message: str


@app.post("/chat")
def chat(payload: ChatMessage):
    understanding = understand_message(payload.message)
    target_date = resolve_date(understanding.get("date_hint"))

    if understanding["intent"] == "check_availability":
        return {
            "reply": understanding["reply"],
            "intent": understanding["intent"],
            "available_slots": get_available_slots(target_date),
        }

    if understanding["intent"] == "book":
        customer_name = understanding.get("customer_name")
        time_hint = understanding.get("time_hint")

        if not customer_name or not time_hint:
            return {"reply": understanding["reply"], "intent": "book", "booked": False}

        hour, minute = map(int, time_hint.split(":"))
        requested_time = datetime.combine(target_date, datetime.min.time()).replace(
            hour=hour, minute=minute
        )

        error = validate_booking_time(requested_time)
        if error:
            return {"reply": error, "intent": "book", "booked": False}

        new_appointment = Appointment(
            id=str(uuid.uuid4()),
            customer_name=customer_name,
            customer_contact="from_chat",
            start_time=requested_time,
        )
        appointments_db[new_appointment.id] = new_appointment

        return {
            "reply": f"You're all set, {customer_name}! Booked for {requested_time.strftime('%Y-%m-%d %H:%M')}.",
            "intent": "book",
            "booked": True,
            "appointment_id": new_appointment.id,
        }

    return {"reply": understanding["reply"], "intent": understanding["intent"]}