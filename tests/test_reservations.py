import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from bus_ticket_reservation.catalog import SERVICES_BY_CODE, find_services, validate_travel_date
from bus_ticket_reservation.storage import ReservationError, ReservationStore


ROOT = Path(__file__).resolve().parents[1]


class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = ReservationStore(Path(self.temp_dir.name) / "bookings.sqlite3")
        self.travel_date = date.today() + timedelta(days=1)

    def test_booking_lookup_cancellation_and_rebooking(self):
        first = self.store.book("B101", self.travel_date, 7, "Ada Lovelace", "+60123456789")
        self.assertEqual(self.store.occupied_seats("B101", self.travel_date), {7})
        self.assertIsNone(self.store.get_booking(first.reference, "60123456789"))
        self.assertEqual(self.store.get_booking(first.reference.lower(), "+60123456789"), first)

        with self.assertRaisesRegex(ReservationError, "just taken"):
            self.store.book("B101", self.travel_date, 7, "Grace Hopper", "+60123456780")

        cancelled = self.store.cancel(first.reference, "+60123456789")
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(self.store.occupied_seats("B101", self.travel_date), set())
        with self.assertRaisesRegex(ReservationError, "already cancelled"):
            self.store.cancel(first.reference, "+60123456789")

        second = self.store.book("B101", self.travel_date, 7, "Grace Hopper", "+60123456780")
        self.assertNotEqual(first.reference, second.reference)
        self.assertEqual(self.store.occupied_seats("B101", self.travel_date), {7})

    def test_validation_rejects_invalid_values(self):
        cases = [
            ("X999", self.travel_date, 1, "Ada Lovelace", "+60123456789"),
            ("B101", self.travel_date, 0, "Ada Lovelace", "+60123456789"),
            ("B101", self.travel_date, 25, "Ada Lovelace", "+60123456789"),
            ("B101", self.travel_date, 1, "A", "+60123456789"),
            ("B101", self.travel_date, 1, "Ada Lovelace", "abc"),
            ("B101", date.today() - timedelta(days=1), 1, "Ada Lovelace", "+60123456789"),
        ]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ReservationError):
                self.store.book(*values)

    def test_simultaneous_requests_cannot_take_the_same_seat(self):
        start = threading.Barrier(2)

        def reserve(name, phone):
            start.wait()
            try:
                return self.store.book("B101", self.travel_date, 9, name, phone)
            except ReservationError as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda details: reserve(*details),
                [("Ada Lovelace", "+60123456789"), ("Grace Hopper", "+60123456780")],
            ))
        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(self.store.occupied_seats("B101", self.travel_date), {9})

    def test_timetable_and_date_window(self):
        self.assertEqual(validate_travel_date(self.travel_date.isoformat()), self.travel_date)
        with self.assertRaises(ValueError):
            validate_travel_date("2026-99-99")
        with self.assertRaises(ValueError):
            validate_travel_date((date.today() + timedelta(days=30)).isoformat())
        matches = find_services("Kuala Lumpur", "Ipoh", self.travel_date)
        self.assertEqual([service.code for service in matches], ["B101", "B102"])
        self.assertEqual(SERVICES_BY_CODE["B101"].arrival_at(self.travel_date).hour, 10)

    def test_menu_booking_and_cancellation(self):
        database_path = Path(self.temp_dir.name) / "cli.sqlite3"
        env = {**os.environ, "BUS_TICKET_DB": str(database_path), "NO_COLOR": "1"}
        travel_date = self.travel_date.isoformat()
        booking_input = f"1\n1\n1\n{travel_date}\n1\n4\nAda Lovelace\n+60123456789\nYES\n5\n"
        completed = subprocess.run(
            [sys.executable, "main.py"], input=booking_input, text=True,
            capture_output=True, cwd=ROOT, env=env, check=True,
        )
        self.assertIn("YOUR TICKET", completed.stdout)
        reference = re.search(r"BT-[A-F0-9]{10}", completed.stdout)
        self.assertIsNotNone(reference)
        self.assertIn(4, ReservationStore(database_path).occupied_seats("B101", self.travel_date))

        cancel_input = f"3\n{reference.group()}\n+60123456789\nCANCEL\n5\n"
        cancelled = subprocess.run(
            [sys.executable, "-m", "bus_ticket_reservation"], input=cancel_input,
            text=True, capture_output=True, cwd=ROOT, env=env, check=True,
        )
        self.assertIn("is available again", cancelled.stdout)
        self.assertEqual(ReservationStore(database_path).occupied_seats("B101", self.travel_date), set())


if __name__ == "__main__":
    unittest.main()
