from datetime import date, datetime, timedelta
from app.storage import appointments_db

WORK_START_HOUR = 9
WORK_END_HOUR = 18
SLOT_MINUTES = 30


def get_available_slots(target_date: date) -> list[datetime]:
    booked_times = {a.start_time for a in appointments_db.values()}

    day_start = datetime.combine(target_date, datetime.min.time()).replace(hour=WORK_START_HOUR)
    day_end = datetime.combine(target_date, datetime.min.time()).replace(hour=WORK_END_HOUR)

    slots = []
    current = day_start
    while current < day_end:
        if current not in booked_times:
            slots.append(current)
        current += timedelta(minutes=SLOT_MINUTES)

    return slots


def validate_booking_time(requested_time: datetime) -> str | None:
    """Returns an error message if the time is invalid, otherwise None."""
    if requested_time.hour < WORK_START_HOUR or requested_time.hour >= WORK_END_HOUR:
        return f"Booking must be between {WORK_START_HOUR}:00 and {WORK_END_HOUR}:00."

    for existing in appointments_db.values():
        if existing.start_time == requested_time:
            return "This time slot is already booked. Please choose another time."

    return None