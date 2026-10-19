"""Step 3 — safe, schema-aware SQLite reader shared by the three tools.

Works without an LLM or API key. All SQL is executed on a SQLite database
opened with mode=ro, query_only, and a restrictive authorization callback.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import time


MAX_RESULTS = 20
MAX_CELL_CHARS = 250
QUERY_TIMEOUT_SECONDS = 8.0


@dataclass(frozen=True)
class DatabaseConfig:
    table: str
    db_filename: str
    tool_name: str
    scope: str
    caution: str


DATABASES: dict[str, DatabaseConfig] = {
    "institutions": DatabaseConfig(
        table="institutions",
        db_filename="institutions.db",
        tool_name="InstitutionsDBTool",
        scope="Bangladesh educational institution names, EIIN identifiers, education levels, types, divisions, districts, and addresses",
        caution=("This dataset is mainly educational institutions; it does not establish the total number "
                 "of all government organizations in Bangladesh."),
    ),
    "hospitals": DatabaseConfig(
        table="hospitals",
        db_filename="hospitals.db",
        tool_name="HospitalsDBTool",
        scope="Bangladesh health-facility names, types, agencies, divisions, districts, and public/private flags",
        caution=("Records include health offices and other facilities, not only hospitals. "
                 "Hospital totals require filtering the type field. Beds, doctors and facilities are "
                 "not provided as explicit columns."),
    ),
    "restaurants": DatabaseConfig(
        table="restaurants",
        db_filename="restaurants.db",
        tool_name="RestaurantsDBTool",
        scope="Bangladesh food-place names, addresses, coordinates, ratings and review counts",
        caution=("The source includes some non-restaurant places; an unfiltered row count is not "
                 "a verified restaurant total. Cuisine is not an explicit column. Some ratings "
                 "are missing or zero."),
    ),
}


class QueryRejected(ValueError):
    """SQL is not allowed by this read-only tool."""


def _validate_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise QueryRejected("Provide a nonempty SQL SELECT statement.")
    query = sql.strip()
    if query.endswith(";"):
        query = query[:-1].rstrip()
    if not re.match(r"(?is)^SELECT\s", query):
        raise QueryRejected("Only one SELECT query is allowed (no writes, PRAGMA, or CTEs).")
    if any(token in query for token in (";", "--", "/*", "*/", "\x00")):
        raise QueryRejected("Multiple statements, comments and NUL characters are not allowed.")
    if len(query) > 5000:
        raise QueryRejected("SQL query is too long (maximum 5000 characters).")
    return query


def _stringify(value: object) -> str:
    if value is None:
        return "NULL"
    rendered = str(value).replace("\n", " ").replace("\r", " ")
    if len(rendered) > MAX_CELL_CHARS:
        return rendered[:MAX_CELL_CHARS] + "…"
    return rendered


class ReadOnlySQLite:
    def __init__(self, project_root: Path, config: DatabaseConfig):
        self.project_root = Path(project_root).resolve()
        self.config = config
        self.path = self.project_root / "databases" / config.db_filename
        if not self.path.is_file():
            raise FileNotFoundError(
                f"Missing database: {self.path}. Complete Step 2 before running Step 3."
            )
        self.columns = self._read_schema()
        if not self.columns:
            raise RuntimeError(f"Table {config.table!r} not found in {self.path}")

    def _connect(self):
        conn = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return conn

    def _read_schema(self) -> dict[str, str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(f'PRAGMA table_info("{self.config.table}")').fetchall()
        return {row["name"]: row["type"] for row in rows}

    def schema_description(self) -> str:
        return ", ".join(f"{name} {affinity}" for name, affinity in self.columns.items())

    def execute(self, sql: str) -> str:
        """Return a short natural-language summary of rows retrieved by safe SQL."""
        try:
            query = _validate_sql(sql)
        except QueryRejected as error:
            return f"Query rejected: {error}"

        table = self.config.table
        deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
        authorized_table_read = False

        def authorize(action: int, arg1: str | None, arg2: str | None,
                      dbname: str | None, origin: str | None) -> int:
            nonlocal authorized_table_read
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ:
                if arg1 and arg1.casefold() == table.casefold():
                    authorized_table_read = True
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION:
                # Only commonly needed numeric, text, and aggregate functions.
                allowed = {
                    "count", "sum", "avg", "min", "max", "total", "round",
                    "lower", "upper", "trim", "ltrim", "rtrim", "length", "substr",
                    "coalesce", "ifnull", "nullif", "abs", "like", "glob",
                    "replace", "cast", "typeof"
                }
                return sqlite3.SQLITE_OK if (arg2 or "").casefold() in allowed else sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_DENY

        def progress() -> int:
            return 1 if time.monotonic() > deadline else 0

        try:
            with closing(self._connect()) as conn:
                conn.set_authorizer(authorize)
                conn.set_progress_handler(progress, 1000)
                cursor = conn.execute(query)
                result = cursor.fetchmany(MAX_RESULTS + 1)
                names = [column[0] for column in cursor.description or []]
            if not authorized_table_read:
                return f"Query rejected: SELECT must read from the {table} table."
            return self._format_rows(result, names)
        except sqlite3.Error as error:
            # Do not expose absolute local filesystem paths in tool responses.
            message = str(error)
            return (f"SQL error: {table} database: {message}. "
                    f"Available columns: {', '.join(self.columns)}")

    def _format_rows(self, rows: list[sqlite3.Row], names: list[str]) -> str:
        table = self.config.table
        if not rows:
            return f"No matching records found in the {table} dataset."
        shown = rows[:MAX_RESULTS]
        more = len(rows) > MAX_RESULTS
        if len(shown) == 1 and len(names) == 1 and not more:
            return (f"From the {table} dataset, {_stringify(names[0])} = "
                    f"{_stringify(shown[0][0])}. This describes dataset records, not an "
                    f"independently verified national total.")
        intro = f"From the {table} dataset, the SQL query returned"
        intro += f" at least {MAX_RESULTS + 1} rows; showing the first {MAX_RESULTS}:" if more else f" {len(shown)} row(s):"
        lines = [intro]
        for index, row in enumerate(shown, 1):
            cells = ", ".join(f"{_stringify(name)}: {_stringify(row[position])}"
                              for position, name in enumerate(names))
            lines.append(f"{index}. {cells}")
        if more:
            lines.append("More rows exist. Refine the SQL WHERE clause or aggregation for a precise answer.")
        return "\n".join(lines)
