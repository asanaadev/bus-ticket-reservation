from __future__ import annotations

import re
import secrets
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .catalog import SERVICES_BY_CODE, Service, is_bookable, validate_travel_date


class ReservationError(Exception):
    pass


@dataclass(frozen=True)
class Booking:
    reference: str
    service: Service
    travel_date: date
    seat: int
    name: str
    phone: str
    status: str
    created_at: str


def validate_name(value: str) -> str:
    name = " ".join(value.split())
    if not 2 <= len(name) <= 60 or any(ord(char) < 32 for char in name):
        raise ReservationError("Passenger name must be 2 to 60 characters.")
    return name


def validate_phone(value: str) -> str:
    phone = value.strip().replace(" ", "").replace("-", "")
    if not re.fullmatch(r"\+?[0-9]{7,15}", phone):
        raise ReservationError("Enter a phone number with 7–15 digits; a leading + is allowed.")
    return phone


class ReservationStore:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS bookings (
                    reference TEXT PRIMARY KEY,
                    service_code TEXT NOT NULL,
                    travel_date TEXT NOT NULL,
                    seat INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
                    created_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_confirmed_booking_per_seat
                    ON bookings(service_code, travel_date, seat)
                    WHERE status = 'confirmed';
            """)

    def occupied_seats(self, service_code: str, travel_date: date) -> set[int]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                "SELECT seat FROM bookings WHERE service_code = ? AND travel_date = ? AND status = 'confirmed'",
                (service_code, travel_date.isoformat()),
            ).fetchall()
        return {row["seat"] for row in rows}

    def book(self, service_code: str, travel_date: date, seat: int, name: str, phone: str) -> Booking:
        service = SERVICES_BY_CODE.get(service_code)
        if service is None:
            raise ReservationError("Select a listed bus service.")
        try:
            validate_travel_date(travel_date.isoformat())
        except ValueError as exc:
            raise ReservationError(str(exc)) from exc
        if not is_bookable(service, travel_date):
            raise ReservationError("This bus has already departed.")
        if type(seat) is not int or not 1 <= seat <= service.seats:
            raise ReservationError(f"Choose a seat from 1 to {service.seats}.")
        name = validate_name(name)
        phone = validate_phone(phone)
        created_at = datetime.now().isoformat(timespec="seconds")

        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                taken = connection.execute(
                    "SELECT 1 FROM bookings WHERE service_code = ? AND travel_date = ? AND seat = ? AND status = 'confirmed'",
                    (service_code, travel_date.isoformat(), seat),
                ).fetchone()
                if taken:
                    raise ReservationError("That seat was just taken. Please choose another.")
                reference = "BT-" + secrets.token_hex(5).upper()
                connection.execute(
                    "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?)",
                    (reference, service_code, travel_date.isoformat(), seat, name, phone, created_at),
                )
        except sqlite3.IntegrityError as exc:
            raise ReservationError("The booking could not be saved. Please try again.") from exc
        return Booking(reference, service, travel_date, seat, name, phone, "confirmed", created_at)

    def get_booking(self, reference: str, phone: str) -> Booking | None:
        phone = validate_phone(phone)
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT * FROM bookings WHERE reference = ? AND phone = ?",
                (reference.strip().upper(), phone),
            ).fetchone()
        return self._to_booking(row) if row else None

    def cancel(self, reference: str, phone: str) -> Booking:
        phone = validate_phone(phone)
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM bookings WHERE reference = ? AND phone = ?",
                (reference.strip().upper(), phone),
            ).fetchone()
            if row is None:
                raise ReservationError("No booking matched that reference and phone number.")
            if row["status"] == "cancelled":
                raise ReservationError("This booking is already cancelled.")
            connection.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE reference = ?",
                (row["reference"],),
            )
        return self._to_booking(row, status="cancelled")

    @staticmethod
    def _to_booking(row: sqlite3.Row, *, status: str | None = None) -> Booking:
        return Booking(
            row["reference"], SERVICES_BY_CODE[row["service_code"]],
            date.fromisoformat(row["travel_date"]), row["seat"], row["name"],
            row["phone"], status or row["status"], row["created_at"],
        )
