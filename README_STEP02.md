# Step 2 — CSV → SQLite (Windows file-lock fix)

This package is intended to be extracted into the **existing** `D:\Multi_Tool_AI_Agent_Bangladesh` project. It adds files in `scripts/` and `tests/` and does not replace any Step 1 configuration.

## Prerequisites

Open VS Code Terminal (PowerShell) in the project root and activate the existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install pandas huggingface_hub pytest
```

## Fix for WinError 32 (SQLite temporary file)

This updated package explicitly **closes** the temporary SQLite database connection before `Path.replace()`. This prevents a Windows file-lock error caused by the original version of the build script. **If all three datasets are already saved locally**, avoid network access:

```powershell
python scripts/step02_build_databases.py --skip-download
```

**If the first run stopped after institutions (as in WinError 32)**, use the normal command instead, since hospitals and restaurants may not yet have been downloaded:

```powershell
python scripts/step02_build_databases.py
```

The Hugging Face downloader can reuse cached content already downloaded.

If file locking persists, close any SQLite database viewer / VS Code SQLite extension that has opened `.db` or `.db.tmp` files before rerunning. The script does not require deleting your source CSV files or reinstalling Python.

## Download and build

```powershell
python scripts/step02_build_databases.py
```

Three CSV repositories are downloaded from Hugging Face to `data/raw/{institutions,hospitals,restaurants}`. The script imports their actual original columns into three separate SQLite databases in `databases/`, preserving NULLs and checking numeric types. It writes `data/step02_audit_report.json`.

If Hugging Face is blocked, manually obtain CSVs from the three dataset pages and place them in `data/raw/institutions/`, `data/raw/hospitals/`, and `data/raw/restaurants/`, then:

```powershell
python scripts/step02_build_databases.py --skip-download
```

## Verify

```powershell
python scripts/step02_verify_databases.py
python -m pytest -q tests/test_step02_sample.py
```

The pytest uses **synthetic CSVs** in a temporary directory for testing. It does not prove remote downloads worked; the live download/build does that.

## Dataset notes

- The **institutions** data contains educational institutions, not necessarily all government institutions or universities.
- The **hospitals** data includes many health offices, clinics, and other health facilities; `COUNT(*)` is **not** the number of hospitals. Beds, physician counts, and facility details are not explicit columns.
- The **restaurants** CSV preview contains some clearly non-restaurant businesses/places, so do not equate `COUNT(*)` with a validated count of restaurants. No cuisine column. `rating=0` should not be blindly treated as a rated zero-star review.
- No fake capacities, bed counts, or cuisines are generated.
- Column mappings derive from the Hugging Face previews as inspected in October 2026. If a repository changes, script stops with a clear schema error instead of silently fabricating columns.
- Do not upload API keys or `.env` to GitHub. Also check dataset reuse licenses and content before committing raw copies of datasets to public GitHub.

## Source datasets

- https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh
- https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals
- https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data
