# Busline — Bus Ticket Reservation

A clean, menu-driven bus ticket reservation demo built with **Python's standard library only**. Search sample daily services, see the seat map, reserve a seat, retrieve a ticket, and cancel a booking. Reservations are saved in SQLite, so they remain available after you close the app.

> **Demo data:** Routes, departure times, and fares are examples. This app has no connection to a bus operator and does not collect payments.

## Quick start

Requires Python **3.9 or newer**. No packages to install.

```bash
cd bus-ticket-reservation
python3 main.py
```

You can also run `python3 -m bus_ticket_reservation` from the project folder. On Windows, use `python` or `py` if `python3` is unavailable.

The main menu offers:

1. Find a bus and reserve a seat
2. Find a booking using its reference and phone number
3. Cancel a booking and release its seat
4. Read about the demo
5. Exit

Choose a route and a date, then pick an available seat. Confirming a reservation displays a ticket with a unique reference. **Save the reference and phone number** to find or cancel it later. Dates can be booked from today through the next 29 days. A departure disappears once its scheduled local time has passed.

## Where bookings are stored

The app creates `data/bookings.sqlite3` on first launch. This file is ignored by Git, so your personal bookings stay out of the repository. To use another location, set `BUS_TICKET_DB` to a writable file path:

```bash
BUS_TICKET_DB=/path/to/my-bookings.sqlite3 python3 main.py
```

The displayed times follow your computer's local clock. The seat count is enforced by a SQLite transaction and unique index, including when two app instances try to reserve the same seat.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests cover validation, the booking window, duplicate seat prevention, retrieval, cancellation, seat reuse, and a full terminal booking and cancellation flow. Test databases are created in temporary folders.

## Project structure

```text
bus-ticket-reservation/
├── main.py                         Simple launch script
├── bus_ticket_reservation/
│   ├── __main__.py                 Startup and database path
│   ├── catalog.py                  Sample routes, fares, and dates
│   ├── cli.py                      Menu, seat map, and ticket display
│   └── storage.py                  SQLite and reservation rules
├── tests/test_reservations.py       Automated tests
├── data/                            Local database folder
├── REPORT.md                        Reflective technical report
└── pyproject.toml                   Project metadata
```

To change the sample timetable, edit `SERVICES` in `bus_ticket_reservation/catalog.py`. Each listed service runs daily within the 30-day booking window.
