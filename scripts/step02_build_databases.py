"""Step 02: Download 3 Hugging Face CSV datasets and build typed SQLite DBs.

Run from the project's root:
    python scripts/step02_build_databases.py
    python scripts/step02_build_databases.py --skip-download

Only the original, observed columns are imported. No missing medical or
restaurant attributes are invented. SQLite files are replaced atomically.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

# Source column name -> (SQL column name, explicit SQLite column type)
DATASETS = {
    "institutions": {
        "repo": "Mahadih534/Institutional-Information-of-Bangladesh",
        "table": "institutions",
        "identifier": "eiin",
        "columns": {
            "INSTITUTE NAME": ("name", "TEXT"),
            "EIIN": ("eiin", "INTEGER"),
            "INSTITUTE_TYPE": ("type", "TEXT"),
            "DIVISION_ID": ("division_id", "INTEGER"),
            "DIVISION": ("division", "TEXT"),
            "DISTRICT_ID": ("district_id", "INTEGER"),
            "DISTRICT": ("district", "TEXT"),
            "THANA_ID": ("thana_id", "INTEGER"),
            "THANA": ("thana", "TEXT"),
            "UNION_ID": ("union_id", "INTEGER"),
            "UNION_NAME": ("union_name", "TEXT"),
            "MAUZA_ID": ("mauza_id", "INTEGER"),
            "MAUZA_NAME": ("mauza_name", "TEXT"),
            "AREA_STATUS": ("area_status", "TEXT"),
            "GEOGRPYCAL_STATUS": ("geographical_status", "TEXT"),
            "ADDRESS": ("address", "TEXT"),
            "POST": ("post", "TEXT"),
            "MANAGEMENT_TYPE": ("management_type", "TEXT"),
            "MOBILE": ("mobile", "TEXT"),
            "STUDENT_TYPE": ("student_type", "TEXT"),
            "EDUCATION_LEVEL": ("education_level", "TEXT"),
            "AFFILIATION": ("affiliation", "TEXT"),
            "MPO_STATUS": ("mpo_status", "TEXT"),
        },
        "indexes": ["name", "type", "division", "district"],
    },
    "hospitals": {
        "repo": "Mahadih534/all-bangladeshi-hospitals",
        "table": "hospitals",
        "identifier": "code",
        "columns": {
            "Id": ("id", "INTEGER"),
            "Name": ("name", "TEXT"),
            "Name (Bangla)": ("name_bn", "TEXT"),
            "Code": ("code", "INTEGER"),
            "Agency": ("agency", "TEXT"),
            "Type": ("type", "TEXT"),
            "Division": ("division", "TEXT"),
            "District": ("district", "TEXT"),
            "City Corporation": ("city_corporation", "TEXT"),
            "Upazila": ("upazila", "TEXT"),
            "Paurasava": ("paurasava", "TEXT"),
            "Union": ("union_name", "TEXT"),
            "Private": ("is_private", "INTEGER"),
        },
        "indexes": ["name", "type", "division", "district"],
    },
    "restaurants": {
        "repo": "Mahadih534/Bangladeshi-Restaurant-Data",
        "table": "restaurants",
        "identifier": "place_id",
        "columns": {
            "place_id": ("place_id", "TEXT"),
            "name": ("name", "TEXT"),
            "latitude": ("latitude", "REAL"),
            "longitude": ("longitude", "REAL"),
            "rating": ("rating", "REAL"),
            "number_of_reviews": ("number_of_reviews", "INTEGER"),
            "affluence": ("affluence", "REAL"),
            "address": ("address", "TEXT"),
        },
        "indexes": ["name", "rating", "address"],
    },
}


def normalize_header(header: str) -> str:
    """Compare headers ignoring whitespace, punctuation, case and UTF-8 BOM."""
    return re.sub(r"[^a-z0-9]", "", header.lower().lstrip("\ufeff"))


def read_csv(path: Path) -> pd.DataFrame:
    # dtype=str prevents accidental conversion of telephone numbers to integers.
    # keep_default_na=False avoids treating legitimate 'N/A' locations as null.
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    frame.columns = [str(x).strip() for x in frame.columns]
    return frame


def clean_and_type(source: pd.DataFrame, spec: dict, path: Path) -> pd.DataFrame:
    lookup: dict[str, str] = {}
    for header in source.columns:
        key = normalize_header(header)
        if key in lookup:
            raise ValueError(f"Duplicate/equivalent headers in {path}: {lookup[key]} and {header}")
        lookup[key] = header

    expected = spec["columns"]
    missing = [header for header in expected if normalize_header(header) not in lookup]
    if missing:
        raise ValueError(
            f"{path.name}: Expected CSV columns not found: {missing}.\n"
            f"Actual CSV columns: {list(source.columns)}\n"
            "Check the Hugging Face dataset's schema before changing the mapping."
        )

    unknown = [h for h in source.columns if normalize_header(h) not in {normalize_header(e) for e in expected}]
    if unknown:
        print(f"    WARNING: Extra source columns not imported: {unknown}")

    output = pd.DataFrame(index=source.index)
    for original, (target, kind) in expected.items():
        values = source[lookup[normalize_header(original)]].astype("string").str.strip()
        missing_value = values.isna() | values.str.lower().isin(("", "null", "none", "nan", "<na>"))
        values = values.mask(missing_value, pd.NA)

        if kind == "TEXT":
            output[target] = values.astype(object).where(values.notna(), None)
            continue

        # Allow thousands separators only in explicitly numeric columns.
        parsed = pd.to_numeric(values.str.replace(",", "", regex=False), errors="coerce")
        invalid = values.notna() & parsed.isna()
        if invalid.any():
            examples = values.loc[invalid].head(5).tolist()
            raise ValueError(f"{path.name}: Non-numeric values in {original}: {examples}")

        if kind == "INTEGER":
            non_integral = parsed.notna() & (parsed != parsed.round())
            if non_integral.any():
                examples = values.loc[non_integral].head(5).tolist()
                raise ValueError(f"{path.name}: Fractional values in INTEGER column {original}: {examples}")
            output[target] = parsed.astype("Int64")
        elif kind == "REAL":
            output[target] = parsed.astype("Float64")
        else:
            raise ValueError(f"Unsupported SQLite type: {kind}")
    return output


def download_csv_files(dataset_key: str, repo: str, root: Path, skip_download: bool) -> list[Path]:
    directory = root / "data" / "raw" / dataset_key
    directory.mkdir(parents=True, exist_ok=True)

    if not skip_download:
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=repo,
                repo_type="dataset",
                local_dir=str(directory),
                allow_patterns=["*.csv", "*.CSV", "**/*.csv", "**/*.CSV"],
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not download {repo}. Check your network or Hugging Face access.\n"
                f"If CSV files are already inside {directory}, rerun with --skip-download."
            ) from exc

    files = sorted(x for x in directory.rglob("*") if x.is_file() and x.suffix.lower() == ".csv")
    if not files:
        raise FileNotFoundError(f"No CSV files found under: {directory}")
    return files


def build_database(key: str, spec: dict, root: Path, skip_download: bool) -> dict:
    print(f"\n=== {key.upper()} ===")
    paths = download_csv_files(key, spec["repo"], root, skip_download)
    print("  CSV files:", ", ".join(str(p.relative_to(root)) for p in paths))

    parts = []
    input_rows = 0
    for path in paths:
        source = read_csv(path)
        input_rows += len(source)
        print(f"  Reading {path.name}: {len(source):,} rows")
        parts.append(clean_and_type(source, spec, path))

    frame = pd.concat(parts, ignore_index=True)
    output_dir = root / "databases"
    output_dir.mkdir(parents=True, exist_ok=True)
    final_db = output_dir / f"{key}.db"
    temp_db = output_dir / f"{key}.db.tmp"
    temp_db.unlink(missing_ok=True)

    table = spec["table"]  # predefined, not supplied by user
    columns = {target: kind for target, kind in spec["columns"].values()}
    create_sql = f"CREATE TABLE {table} (" + ", ".join(
        f'"{column}" {kind}' for column, kind in columns.items()
    ) + ")"

    try:
        # sqlite3.Connection as a context manager commits/rolls back transactions
        # but DOES NOT close the connection. On Windows an open SQLite handle
        # prevents os.replace() from renaming the temporary database file.
        with closing(sqlite3.connect(temp_db)) as conn:
            with conn:
                conn.execute(create_sql)
                # Explicit CREATE TABLE ensures SQLite column affinities exactly match spec.
                frame.to_sql(table, conn, if_exists="append", index=False, chunksize=1000)
                for idx_column in spec["indexes"]:
                    conn.execute(f'CREATE INDEX "idx_{table}_{idx_column}" ON "{table}" ("{idx_column}")')
                actual_rows = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                types = {row[1]: row[2] for row in conn.execute(f'PRAGMA table_info("{table}")')}
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                if actual_rows != len(frame) or actual_rows != input_rows:
                    raise RuntimeError(f"Row count mismatch! CSV={input_rows}, SQLite={actual_rows}")
                if types != columns:
                    raise RuntimeError(f"Column type mismatch! Expected: {columns}; found: {types}")
                if integrity != "ok":
                    raise RuntimeError(f"SQLite integrity failed: {integrity}")
        # The file is closed *before* rename, including on the Windows platform.
        temp_db.replace(final_db)
    except Exception:
        # Cleanup should not hide a useful failure, e.g. if another program
        # (VS Code SQLite extension / DB Browser) has locked the temp file.
        try:
            temp_db.unlink(missing_ok=True)
        except PermissionError:
            print(f"  WARNING: Could not remove locked temporary database: {temp_db}")
        raise

    identifier = spec["identifier"]
    duplicate_ids = int(frame[identifier].dropna().duplicated().sum())
    print(f"  Created {final_db.relative_to(root)}: {len(frame):,} rows, {len(columns)} columns")
    print(f"  Duplicate non-null {identifier} values: {duplicate_ids} (retained, not silently removed)")

    return {
        "dataset": key,
        "source_repo": spec["repo"],
        "csv_files": [str(p.relative_to(root)) for p in paths],
        "source_rows": input_rows,
        "imported_rows": len(frame),
        "sqlite_path": str(final_db.relative_to(root)),
        "table": table,
        "column_types": columns,
        "missing_by_column": {col: int(frame[col].isna().sum()) for col in frame.columns},
        "duplicate_identifier_values": duplicate_ids,
        "identifier": identifier,
    }


def run(root: Path, skip_download: bool = False) -> dict:
    root = root.resolve()
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Dataset row counts describe CSV records, not verified real-world entity totals.",
        "datasets": {},
    }
    for key, spec in DATASETS.items():
        report["datasets"][key] = build_database(key, spec, root, skip_download)

    report_path = root / "data" / "step02_audit_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAudit report: {report_path}")
    print("STEP 2 SUCCESSFUL — 3 SQLite databases verified.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build typed SQLite databases from Bangladesh CSV datasets")
    parser.add_argument("--skip-download", action="store_true", help="Use CSVs already saved in data/raw/<dataset>/")
    args = parser.parse_args()
    run(ROOT, skip_download=args.skip_download)
