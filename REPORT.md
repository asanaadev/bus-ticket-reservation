# Reflective Technical Report: Bus Ticket Reservation

## 1. Introduction

Computational thinking helps turn an everyday activity into steps a computer can carry out reliably. Reserving a bus seat involves a timetable, route choices, date and time checks, available seats, passenger details, and cancellation rules. Breaking those concerns apart makes the problem easier to implement, test, and explain. It also helps prevent mistakes such as assigning one seat to two passengers.

## 2. Task Overview

The task was to develop a Python bus ticket reservation application with a menu-driven interface, modular code, input validation, and persistent data. The main challenge was making the booking process clear to a user while preserving correct seat availability when the program is reopened or run twice at the same time.

The completed application, **Busline**, is an offline terminal demo. A passenger can search sample daily services, view a seat map, book a seat, retrieve a ticket, and cancel a reservation. It addresses the practical problem of tracking who has reserved each seat on a particular service and date. Its routes and prices are illustrative; it does not connect to a real bus company or take payment.

## 3. Problem Analysis

**Problem solved.** Paper lists or temporary in-memory data can lose bookings and make seat conflicts hard to spot. The application stores confirmed reservations in SQLite and checks availability before saving a booking. Cancelling changes the booking status and frees the seat.

**Importance.** Accurate seat counts and a predictable booking flow reduce passenger confusion. Persistent records let a passenger return later with a reference and phone number to inspect or cancel a ticket.

**Expected users.** The primary users are students demonstrating Python fundamentals and people exploring a simple reservation flow. The sample timetable also makes the program suitable for showing to friends on GitHub. It is not intended for real passengers or production operations.

## 4. Python Implementation

**Program flow.** `main.py` starts the package. The app opens or creates a local SQLite database, then repeatedly shows the main menu until the user chooses Exit. Searching asks for an origin, destination, and date. The app filters the timetable to matching future departures, shows the current seat count, and displays a seat map. The user enters a seat and passenger details, then explicitly confirms. On success, the app prints a ticket and reference. Separate menu options retrieve or cancel an existing booking.

**Major functions and modules.** `catalog.py` defines cities, services, prices, the 30-day date rule, and route filtering. `cli.py` handles menus, prompts, seat maps, and ticket output; functions such as `choose`, `search_and_book`, `show_ticket`, and `cancel_booking` keep these tasks separate. `storage.py` defines `ReservationStore`, which creates the database and implements `book`, `get_booking`, `cancel`, and `occupied_seats`. `__main__.py` handles startup and top-level errors.

**Input and output.** Inputs include numbered menu choices, an ISO-format travel date, seat number, passenger name, phone number, and confirmation words. Outputs include matching departures, prices in RM, availability, a seat map, validation messages, and a formatted ticket. A booking reference plus the matching phone number is needed for later lookup or cancellation. Records are stored in `data/bookings.sqlite3` by default.

**Development decisions.** The app uses only the Python standard library, making the quick-start command independent of package downloads. A small editable sample timetable keeps the demonstration self-contained. SQLite provides persistence, a unique index for confirmed seats, and a write transaction that keeps the seat check and booking insert together. The 30-day window and passed-departure check keep the search focused on usable services. Source identifiers are descriptive, while usage guidance and reasoning live in the README and this report.

## 5. Application of Computational Thinking

**Decomposition.** The full reservation problem was divided into timetable rules, passenger interaction, and stored booking rules. Each has its own module, so a timetable change does not require rewriting the database logic.

**Pattern recognition.** Every service uses the same fields: code, origin, destination, departure, duration, fare, and seat capacity. Every booking uses the same reference, service, date, seat, passenger, phone, and status fields. This common structure supports reusable functions instead of separate code for each route.

**Abstraction.** A `Service` represents the information needed to search and display a journey. A `Booking` represents the information needed to show a ticket. The interface does not need to know the SQL statements that save those records.

**Algorithm design.** The search algorithm validates the date, filters services by origin and destination, removes departed services, then subtracts occupied seats from capacity. The booking algorithm validates the input, begins a database write transaction, checks that the selected seat is still free, and inserts the confirmed booking. The unique database index provides a second guard against duplicate confirmed seats. Cancellation changes status, so the same seat becomes available again while the historical record remains.

## 6. Challenges Encountered

**Technical issues.** Availability shown on screen can change before a user confirms. Checking the seat again inside a SQLite write transaction addresses that gap. The app also has to reject dates outside the booking window and seat numbers outside a service's capacity.

**Debugging.** Automated tests exercise duplicate booking, cancellation, rebooking, invalid inputs, date boundaries, and an end-to-end menu session. These tests helped check both the stored state and the user-visible result after each operation.

**Team collaboration.** This version was developed as an individual project, so there was no team handoff or shared code review to reflect on. The modular layout, README, and tests make it easier for future collaborators to understand and change the project.

## 7. Reflection

**Knowledge gained.** A reservation is more than adding a name to a list: dates, status, seat capacity, persistence, and concurrent access all affect correctness. Database constraints are useful even in a small Python application.

**Programming skills improved.** The project practices typed values, lists and dictionaries, input/output, `if`/`else` decisions, loops, functions, modules, exceptions, classes, and SQL queries. It also practices user-friendly terminal output and automated tests.

**Teamwork experience.** There was no team work in this implementation. A useful next step would be asking another person to run the app from the README and review whether the menu and error messages are easy to follow.

**Areas for improvement.** A future version could add multiple passengers per purchase, more route options, receipts, accessibility checks for the seat symbols, and a web or mobile interface. Any real deployment would need operator schedules, proper user authentication, privacy controls, payment integration, and business rules for changes and refunds.

## 8. Conclusion

Busline demonstrates how computational thinking can turn a familiar booking task into a manageable Python program. Its modular design separates schedule data, interface flow, and persistence. The result is a runnable learning project that searches sample trips, reserves seats safely, and retains bookings between sessions.

## 9. Appendix

**GitHub Repository URL:** Add the repository URL here after publishing this project to GitHub. No URL is available before the repository is created.
