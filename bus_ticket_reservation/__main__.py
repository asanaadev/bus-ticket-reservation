import os
import sqlite3
from pathlib import Path

from .cli import run


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    database_path = Path(os.environ.get("BUS_TICKET_DB", project_root / "data" / "bookings.sqlite3"))
    try:
        run(database_path)
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Goodbye!\n")
    except (sqlite3.Error, OSError) as exc:
        print(f"\n  Database error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
