import os
import json
from datetime import date, timedelta
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an appointment booking assistant. Read the customer's \
message and extract ONLY a JSON object, with no extra text, in this exact shape:

{
  "intent": "book" | "check_availability" | "cancel" | "chat",
  "date_hint": "today" | "tomorrow" | null,
  "time_hint": "HH:MM" | null,
  "customer_name": "the customer's name if mentioned, otherwise null",
  "reply": "a short, friendly reply to the customer, in the same language they used"
}

If intent is "book" but customer_name is null, your reply MUST politely ask for \
their name instead of confirming the booking.

Examples:
- "I want to book tomorrow at 10" -> intent: book, date_hint: tomorrow, time_hint: "10:00", customer_name: null, reply asks for their name
- "My name is Sara, book me tomorrow at 10" -> intent: book, date_hint: tomorrow, time_hint: "10:00", customer_name: "Sara"
- "Anything free today?" -> intent: check_availability, date_hint: today, time_hint: null, customer_name: null
"""


def understand_message(message: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


def resolve_date(date_hint: str | None) -> date:
    today = date.today()
    if date_hint == "tomorrow":
        return today + timedelta(days=1)
    return today