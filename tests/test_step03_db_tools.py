"""Synthetic offline Step 3 tests. Does not download datasets or call an LLM."""

from pathlib import Path
import sqlite3

import pytest

from tools.sqlite_readonly import DATABASES, ReadOnlySQLite


@pytest.fixture()
def tiny_root(tmp_path: Path) -> Path:
    db_dir = tmp_path / "databases"
    db_dir.mkdir()
    fixtures = {
        "institutions": (
            "CREATE TABLE institutions (name TEXT, district TEXT, division TEXT, type TEXT, eiin INTEGER)",
            [
                ("College A", "Dhaka", "Dhaka", "College", 101),
                ("School B", "Dhaka", "Dhaka", "School", 102),
                ("College C", "Sylhet", "Sylhet", "College", 103),
            ],
            "INSERT INTO institutions VALUES (?, ?, ?, ?, ?)",
        ),
        "hospitals": (
            "CREATE TABLE hospitals (name TEXT, district TEXT, type TEXT, is_private INTEGER)",
            [
                ("Hospital A", "Dhaka", "Hospital", 0),
                ("Office A", "Dhaka", "Health Office", 0),
            ],
            "INSERT INTO hospitals VALUES (?, ?, ?, ?)",
        ),
        "restaurants": (
            "CREATE TABLE restaurants (name TEXT, address TEXT, rating REAL, number_of_reviews INTEGER)",
            [
                ("Cafe A", "Dhanmondi, Dhaka", 4.4, 25),
                ("Cafe B", "Sylhet", None, 0),
            ],
            "INSERT INTO restaurants VALUES (?, ?, ?, ?)",
        ),
    }
    for key, (create_sql, rows, insert_sql) in fixtures.items():
        with sqlite3.connect(db_dir / DATABASES[key].db_filename) as conn:
            conn.execute(create_sql)
            conn.executemany(insert_sql, rows)
    return tmp_path


def test_tools_query_separate_sqlite_databases(tiny_root):
    for key, expected in (("institutions", "3"), ("hospitals", "2"), ("restaurants", "2")):
        reader = ReadOnlySQLite(tiny_root, DATABASES[key])
        result = reader.execute(f"SELECT COUNT(*) AS records FROM {key}")
        assert f"records = {expected}" in result
        assert reader.columns["name"] == "TEXT"


def test_aggregation_and_text_filters(tiny_root):
    reader = ReadOnlySQLite(tiny_root, DATABASES["institutions"])
    answer = reader.execute(
        "SELECT type, COUNT(*) AS total FROM institutions "
        "WHERE district = 'Dhaka' GROUP BY type ORDER BY type"
    )
    assert "College" in answer and "School" in answer
    assert "total: 1" in answer


def test_write_and_unsafe_queries_rejected(tiny_root):
    reader = ReadOnlySQLite(tiny_root, DATABASES["institutions"])
    bad = [
        "DELETE FROM institutions", "DROP TABLE institutions", "PRAGMA table_info(institutions)",
        "SELECT name FROM institutions; DELETE FROM institutions",
        "WITH r AS (SELECT * FROM institutions) SELECT * FROM r",
        "SELECT name FROM sqlite_master", "SELECT name FROM hospitals",
        "SELECT load_extension('evil') FROM institutions",
    ]
    for query in bad:
        response = reader.execute(query)
        assert response.startswith(("Query rejected:", "SQL error:")), (query, response)
    assert "records = 3" in reader.execute("SELECT COUNT(*) AS records FROM institutions")


def test_unknown_columns_not_fabricated(tiny_root):
    reader = ReadOnlySQLite(tiny_root, DATABASES["hospitals"])
    reply = reader.execute("SELECT beds FROM hospitals")
    assert reply.startswith("SQL error:")
    assert "beds" not in reader.columns


def test_langchain_wrappers(tiny_root):
    pytest.importorskip("langchain_core")
    from tools.db_tools import build_db_tools

    tools = build_db_tools(tiny_root)
    assert {tool.name for tool in tools} == {
        "InstitutionsDBTool", "HospitalsDBTool", "RestaurantsDBTool"
    }
    output = {tool.name: tool.invoke({"sql": f"SELECT COUNT(*) AS records FROM {key}"})
              for key, tool in zip(DATABASES, tools)}
    assert "records = 3" in output["InstitutionsDBTool"]
    assert "records = 2" in output["HospitalsDBTool"]
    assert "records = 2" in output["RestaurantsDBTool"]
    for tool in tools:
        assert "sql" in tool.args
        assert "SELECT" in tool.description
