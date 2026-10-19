"""Verify the 3 SQLite databases and run a few safe read-only SQL queries."""

from pathlib import Path
from contextlib import closing
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
DATA = [
    ("institutions", "institutions.db", "institutions"),
    ("hospitals", "hospitals.db", "hospitals"),
    ("restaurants", "restaurants.db", "restaurants"),
]


def main():
    for title, filename, table in DATA:
        path = ROOT / "databases" / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing DB: {path}. Run step02_build_databases.py first.")
        # URI mode=ro prevents this inspection script from modifying data.
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as con:
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            columns = [f"{row[1]} {row[2]}" for row in con.execute(f'PRAGMA table_info("{table}")')]
            print(f"\n{title.upper()} — {count:,} CSV records")
            print("Columns:", ", ".join(columns))
            if title == "institutions":
                query = "SELECT type, COUNT(*) AS n FROM institutions GROUP BY type ORDER BY n DESC LIMIT 5"
            elif title == "hospitals":
                query = "SELECT type, COUNT(*) AS n FROM hospitals GROUP BY type ORDER BY n DESC LIMIT 5"
            else:
                query = "SELECT name, rating, address FROM restaurants WHERE rating > 0 ORDER BY rating DESC, number_of_reviews DESC LIMIT 5"
            for row in con.execute(query).fetchall():
                print(" ", row)
    print("\nVERIFICATION SUCCESSFUL")


if __name__ == "__main__":
    main()
