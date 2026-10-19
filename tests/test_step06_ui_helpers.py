"""Offline tests: no Groq calls, no Tavily calls, no Streamlit server."""
from __future__ import annotations
import sqlite3
from pathlib import Path

from ui_helpers import completed_turns, validated_sources, safe_error_message, database_counts


def test_completed_turns_last_four_only():
    items = []
    for n in range(7):
        items += [{"role": "user", "content": f"user {n}"}, {"role": "assistant", "content": f"answer {n}"}]
    assert completed_turns(items) == [(f"user {n}", f"answer {n}") for n in range(3, 7)]


def test_ignores_unanswered_user_and_unknown_roles():
    messages = [
        {"role": "system", "content": "not a conversation turn"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "unanswered"},
    ]
    assert completed_turns(messages) == [("one", "reply")]


def test_no_pairs_for_empty_or_unexpected_messages():
    assert completed_turns([{}, "bad", {"role": "assistant", "content": "orphan"}]) == []
    assert completed_turns([], max_pairs=0) == []


def test_sources_keep_only_valid_unique_http():
    urls = ["https://example.org/a", "https://example.org/a", "javascript:alert(1)",
            "http://good.bd/facts", "file:///secret", "https://name:pw@private.invalid/a",
            "https://ex ample.org/a"]
    assert validated_sources(urls) == ["https://example.org/a", "http://good.bd/facts"]


def test_sources_bounded_and_bad_types():
    assert validated_sources("https://example.org") == []
    assert len(validated_sources([f"https://example.org/{i}" for i in range(50)])) == 6


def test_safe_error_does_not_leak_exception_body():
    secret = "gsk_PRIVATE_SECRET_DO_NOT_SHOW"
    assert secret not in safe_error_message(RuntimeError(secret))
    assert "rate limit" in safe_error_message(type("RateLimitError", (Exception,), {})(secret)).lower()
    assert "package" in safe_error_message(ModuleNotFoundError(secret)).lower()


def test_read_real_sqlite_counts(tmp_path: Path):
    dbs = tmp_path / "databases"
    dbs.mkdir()
    for table in ("institutions", "hospitals", "restaurants"):
        with sqlite3.connect(dbs / f"{table}.db") as conn:
            conn.execute(f"CREATE TABLE {table} (name TEXT)")
            conn.execute(f"INSERT INTO {table} (name) VALUES ('example')")
    assert database_counts(tmp_path) == {"institutions": 1, "hospitals": 1, "restaurants": 1}


def test_missing_database_count_is_none(tmp_path: Path):
    assert database_counts(tmp_path) == {"institutions": None, "hospitals": None, "restaurants": None}
