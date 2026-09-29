from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


BOOKING_WINDOW_DAYS = 30
CITIES = ("Kuala Lumpur", "Ipoh", "Penang", "Melaka", "Johor Bahru")


@dataclass(frozen=True)
class Service:
    code: str
    origin: str
    destination: str
    departure: str
    duration_minutes: int
    fare_rm: int
    seats: int = 24

    def departure_at(self, travel_date: date) -> datetime:
        return datetime.combine(travel_date, time.fromisoformat(self.departure))

    def arrival_at(self, travel_date: date) -> datetime:
        return self.departure_at(travel_date) + timedelta(minutes=self.duration_minutes)


SERVICES = (
    Service("B101", "Kuala Lumpur", "Ipoh", "08:00", 150, 28),
    Service("B102", "Kuala Lumpur", "Ipoh", "15:30", 150, 28),
    Service("B201", "Ipoh", "Penang", "10:00", 120, 24),
    Service("B202", "Penang", "Ipoh", "17:00", 120, 24),
    Service("B301", "Kuala Lumpur", "Melaka", "09:00", 135, 22),
    Service("B302", "Melaka", "Kuala Lumpur", "18:00", 135, 22),
    Service("B401", "Kuala Lumpur", "Johor Bahru", "07:30", 270, 45),
    Service("B402", "Johor Bahru", "Kuala Lumpur", "16:00", 270, 45),
    Service("B501", "Ipoh", "Kuala Lumpur", "13:00", 150, 28),
)
SERVICES_BY_CODE = {service.code: service for service in SERVICES}


def validate_travel_date(value: str, *, now: datetime | None = None) -> date:
    try:
        travel_date = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Enter a valid date as YYYY-MM-DD.") from exc
    today = (now or datetime.now()).date()
    if not today <= travel_date < today + timedelta(days=BOOKING_WINDOW_DAYS):
        raise ValueError("Choose a date from today through the next 29 days.")
    return travel_date


def is_bookable(service: Service, travel_date: date, *, now: datetime | None = None) -> bool:
    return service.departure_at(travel_date) > (now or datetime.now())


def find_services(origin: str, destination: str, travel_date: date, *, now: datetime | None = None) -> list[Service]:
    return [
        service for service in SERVICES
        if service.origin == origin
        and service.destination == destination
        and is_bookable(service, travel_date, now=now)
    ]
