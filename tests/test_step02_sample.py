"""Offline self-test with SYNTHETIC data, never represented as actual HF records."""

from pathlib import Path
from contextlib import closing
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from step02_build_databases import DATASETS, run  # noqa: E402


def test_offline_synthetic_build(tmp_path):
    for key, spec in DATASETS.items():
        folder = tmp_path / "data" / "raw" / key
        folder.mkdir(parents=True)
        columns = {}
        for source_name, (sql_name, sql_type) in spec["columns"].items():
            if sql_type == "INTEGER":
                columns[source_name] = ["101", "102"]
            elif sql_type == "REAL":
                columns[source_name] = ["4.5", ""]
            else:
                columns[source_name] = ["ঢাকা Test", ""]
        # Test a critical identifier: contact/mobile remains TEXT.
        if key == "institutions":
            columns["MOBILE"] = ["01712345678", ""]
            columns["EIIN"] = ["100099", "100100"]
        if key == "hospitals":
            columns["Code"] = ["10000001", "10000002"]
        if key == "restaurants":
            columns["place_id"] = ["ChIJ-test-1", "ChIJ-test-2"]
            columns["number_of_reviews"] = ["6", ""]
        pd.DataFrame(columns).to_csv(folder / "sample.csv", index=False, encoding="utf-8-sig")

    report = run(tmp_path, skip_download=True)
    for key, spec in DATASETS.items():
        db = tmp_path / "databases" / f"{key}.db"
        assert db.exists()
        with closing(sqlite3.connect(db)) as con:
            assert con.execute(f'SELECT COUNT(*) FROM "{key}"').fetchone()[0] == 2
            actual = {r[1]: r[2] for r in con.execute(f'PRAGMA table_info("{key}")')}
            assert actual == {name: kind for name, kind in spec["columns"].values()}
            if key == "institutions":
                assert con.execute("SELECT mobile FROM institutions LIMIT 1").fetchone()[0] == "01712345678"
    assert len(report["datasets"]) == 3
    # Run a second time to verify we can safely replace previously built DBs.
    second_report = run(tmp_path, skip_download=True)
    assert len(second_report["datasets"]) == 3
