"""Small, pure helpers for the Step 6 Streamlit UI.

No API key, external provider, or Streamlit import is needed for these functions.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

DATABASE_TABLES = {
    "institutions": "institutions",
    "hospitals": "hospitals",
    "restaurants": "restaurants",
}

EXPECTED_TOOL_NAMES = (
    "InstitutionsDBTool",
    "HospitalsDBTool",
    "RestaurantsDBTool",
    "WebSearchTool",
)


def completed_turns(messages: list[dict], max_pairs: int = 4) -> list[tuple[str, str]]:
    """Return recent *completed* user/assistant pairs for the LangChain prompt.

    Sidebar/help/system messages and an unsent or unfinished user message are
    not fed to the model. Limit context to avoid burning Groq free-plan tokens.
    """
    if max_pairs < 1:
        return []
    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None
    for item in messages:
        if not isinstance(item, dict):
            continue
        role, content = item.get("role"), item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        if role == "user":
            pending_user = content.strip()
        elif role == "assistant" and pending_user is not None:
            pairs.append((pending_user, content.strip()))
            pending_user = None
    return pairs[-max_pairs:]


def validated_sources(values: object, max_count: int = 6) -> list[str]:
    """Allow only unique HTTP(S) URLs; never display arbitrary link schemes."""
    if not isinstance(values, (list, tuple)):
        return []
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or len(value) > 2048:
            continue
        candidate = value.strip()
        if any(c.isspace() for c in candidate):
            continue
        try:
            part = urlsplit(candidate)
        except ValueError:
            continue
        if (part.scheme not in ("http", "https") or not part.netloc
                or part.username is not None or part.password is not None):
            continue
        if candidate not in result:
            result.append(candidate)
        if len(result) >= max_count:
            break
    return result


def safe_error_message(exc: Exception) -> str:
    """Give actionable errors WITHOUT echoing exception details or secrets."""
    label = type(exc).__name__.lower()
    if "ratelimit" in label or "quota" in label:
        return "Groq/Tavily rate limit reached. Please wait and retry later."
    if "authentication" in label or "permission" in label:
        return "API authentication or model access failed. Check your .env and account permissions."
    if "connection" in label or "timeout" in label:
        return "Unable to reach the API. Check your internet connection and try again."
    if "modulenotfound" in label or "importerror" in label:
        return "A Python package is missing. Run: python -m pip install -r requirements.txt"
    if isinstance(exc, FileNotFoundError):
        return "A required SQLite database is missing. Run the Step 2 database build script."
    if isinstance(exc, ValueError):
        return "Please enter a valid question (1 to 3000 characters)."
    return "The request could not be completed. Check your API credits, model access, and terminal logs."


def database_counts(root: Path) -> dict[str, int | None]:
    """Read each real local DB count. No fabricated dashboard statistics."""
    root = Path(root)
    counts: dict[str, int | None] = {}
    for key, table in DATABASE_TABLES.items():
        path = root / "databases" / f"{key}.db"
        if not path.is_file():
            counts[key] = None
            continue
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
                counts[key] = int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        except (sqlite3.Error, OSError, ValueError):
            counts[key] = None
    return counts
