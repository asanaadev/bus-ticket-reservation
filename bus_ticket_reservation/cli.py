from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

from .catalog import CITIES, SERVICES, Service, find_services, validate_travel_date
from .storage import Booking, ReservationError, ReservationStore


WIDTH = 72
COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def style(value: str, code: str) -> str:
    return f"\033[{code}m{value}\033[0m" if COLOR else value


def line(char: str = "─") -> None:
    print(char * WIDTH)


def heading(title: str, subtitle: str = "") -> None:
    print()
    line()
    print(style(f"  {title}", "1;36"))
    if subtitle:
        print(f"  {subtitle}")
    line()


def ask(prompt: str) -> str:
    return input(style(f"  {prompt} ", "1")).strip()


def choose(prompt: str, low: int, high: int) -> int:
    while True:
        value = ask(prompt)
        try:
            selected = int(value)
        except ValueError:
            print("  Please enter a number from the menu.")
            continue
        if low <= selected <= high:
            return selected
        print(f"  Choose a number from {low} to {high}.")


def choose_city(label: str, cities: tuple[str, ...]) -> str | None:
    print(f"\n  {label}")
    for number, city in enumerate(cities, start=1):
        print(f"  {number}. {city}")
    print("  0. Back")
    selection = choose("Select:", 0, len(cities))
    return None if selection == 0 else cities[selection - 1]


def ask_date() -> date:
    while True:
        raw = ask(f"Travel date [YYYY-MM-DD, Enter for today ({date.today()})]:")
        try:
            return validate_travel_date(raw or date.today().isoformat())
        except ValueError as exc:
            print(f"  {exc}")


def seat_map(service: Service, taken: set[int]) -> None:
    print("\n  SEATS                         ◀ front of bus")
    print("  ■ = booked   □ = available")
    for first in range(1, service.seats + 1, 4):
        parts = []
        for number in range(first, min(first + 4, service.seats + 1)):
            symbol = "■" if number in taken else "□"
            parts.append(f"{symbol}{number:02}")
        print("  " + "  ".join(parts[:2]) + "     " + "  ".join(parts[2:]))
    print(f"\n  {service.seats - len(taken)} of {service.seats} seats available")


def show_ticket(booking: Booking) -> None:
    service = booking.service
    heading("YOUR TICKET", f"Reference {booking.reference}  •  {booking.status.upper()}")
    print(f"  Passenger     {booking.name}")
    print(f"  Route         {service.origin} → {service.destination}")
    print(f"  Service       {service.code}")
    print(f"  Departure     {service.departure_at(booking.travel_date):%a, %d %b %Y  %H:%M}")
    print(f"  Arrival       {service.arrival_at(booking.travel_date):%a, %d %b %Y  %H:%M} (estimated)")
    print(f"  Seat          {booking.seat:02d}")
    print(f"  Fare          RM {service.fare_rm:.2f}")
    line()
    print("  Save your reference and phone number to find or cancel this booking.")
    print("  Demo only: no payment is collected and these are sample services.")


def search_and_book(store: ReservationStore) -> None:
    heading("FIND A BUS", "Daily sample departures • bookings open for 30 days")
    origin = choose_city("From", CITIES)
    if origin is None:
        return
    destination = choose_city("To", tuple(city for city in CITIES if city != origin))
    if destination is None:
        return
    travel_date = ask_date()
    matches = find_services(origin, destination, travel_date)
    if not matches:
        print("\n  No upcoming buses match that route and date.")
        print("  Try another route or date.")
        return

    heading("AVAILABLE BUSES", f"{origin} → {destination}  •  {travel_date:%d %b %Y}")
    for number, service in enumerate(matches, start=1):
        free = service.seats - len(store.occupied_seats(service.code, travel_date))
        arrival = service.arrival_at(travel_date)
        print(
            f"  {number}. {service.code}  {service.departure} → {arrival:%H:%M}"
            f"  RM {service.fare_rm:.2f}  {free}/{service.seats} seats"
        )
    print("  0. Back")
    selection = choose("Select a bus:", 0, len(matches))
    if selection == 0:
        return
    service = matches[selection - 1]
    taken = store.occupied_seats(service.code, travel_date)
    if len(taken) == service.seats:
        print("  This bus is full. Please choose another departure.")
        return
    seat_map(service, taken)
    seat = choose("Choose a seat (0 to go back):", 0, service.seats)
    if seat == 0:
        return
    if seat in taken:
        print("  That seat is booked. Please start again and select an available seat.")
        return
    name = ask("Passenger full name:")
    phone = ask("Phone number:")
    print(f"\n  Confirm {name}, seat {seat:02d}, {service.code} on {travel_date}, RM {service.fare_rm:.2f}?")
    if ask("Type YES to confirm:").upper() != "YES":
        print("  Booking discarded.")
        return
    try:
        booking = store.book(service.code, travel_date, seat, name, phone)
    except ReservationError as exc:
        print(f"  Could not book: {exc}")
        return
    show_ticket(booking)


def find_booking(store: ReservationStore) -> None:
    heading("FIND A BOOKING")
    reference = ask("Booking reference:")
    phone = ask("Phone number used when booking:")
    try:
        booking = store.get_booking(reference, phone)
    except ReservationError as exc:
        print(f"  {exc}")
        return
    if booking is None:
        print("  No booking matched that reference and phone number.")
    else:
        show_ticket(booking)


def cancel_booking(store: ReservationStore) -> None:
    heading("CANCEL A BOOKING")
    reference = ask("Booking reference:")
    phone = ask("Phone number used when booking:")
    try:
        booking = store.get_booking(reference, phone)
    except ReservationError as exc:
        print(f"  {exc}")
        return
    if booking is None:
        print("  No booking matched that reference and phone number.")
        return
    if booking.status == "cancelled":
        print("  This booking is already cancelled.")
        return
    show_ticket(booking)
    if ask("Type CANCEL to release this seat:").upper() != "CANCEL":
        print("  Cancellation discarded.")
        return
    try:
        cancelled = store.cancel(reference, phone)
    except ReservationError as exc:
        print(f"  Could not cancel: {exc}")
        return
    print(f"\n  Booking {cancelled.reference} cancelled. Seat {cancelled.seat:02d} is available again.")


def show_about(database_path: Path) -> None:
    heading("ABOUT THIS DEMO")
    print("  A local bus reservation practice project built with Python and SQLite.")
    print("  Timetable and fares are sample data; there is no live inventory or payment.")
    print("  Dates and departure times use your computer's local clock.")
    print(f"  Sample routes: {len(SERVICES)} daily services across {len(CITIES)} cities.")
    print(f"  Bookings database: {database_path}")


def run(database_path: Path) -> None:
    store = ReservationStore(database_path)
    print(style("\n  BUSLINE  /  TICKETS MADE SIMPLE", "1;36"))
    print("  Plan a trip. Pick your seat. Keep your reference.")
    while True:
        heading("MAIN MENU", datetime.now().strftime("%A, %d %B %Y"))
        print("  1. Find a bus & reserve a seat")
        print("  2. Find my booking")
        print("  3. Cancel a booking")
        print("  4. About this demo")
        print("  5. Exit")
        selection = choose("Choose an option:", 1, 5)
        if selection == 1:
            search_and_book(store)
        elif selection == 2:
            find_booking(store)
        elif selection == 3:
            cancel_booking(store)
        elif selection == 4:
            show_about(database_path)
        else:
            print("\n  Thanks for traveling with Busline. Safe travels!\n")
            return
