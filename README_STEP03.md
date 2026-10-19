# Step 3 — Three LangChain SQLite Tools (Windows / VS Code)

This ZIP is a **patch for the project from Steps 1–2**, not a new independent project. Copy its `tools/`, `scripts/`, `tests/` folders into the **existing** `D:\Multi_Tool_AI_Agent_Bangladesh` folder. Merge folders and overwrite matching filenames. The Step 2 `databases/*.db` files are **not** included and should be kept unchanged.

## Prerequisite

Verify your Step 2 command succeeded:

```powershell
python scripts/step02_verify_databases.py
```

Activate Step 1 Python virtual environment:

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
.\.venv\Scripts\Activate.ps1
```

Install any missing Step 3 dependencies:

```powershell
python -m pip install "langchain-core>=1.0,<2" pytest
```

## Run Step 3 tests against real databases

```powershell
python scripts/step03_test_db_tools.py
```

Expected final console line:

```text
STEP 3 SUCCESSFUL — 3 LangChain database tools verified.
```

Then run offline automated tests (synthetic fixtures; no API calls or download):

```powershell
python -m pytest -q tests/test_step03_db_tools.py
```

With langchain-core installed, **5 passed** is expected. The sqlite-only tests can run without LangChain, but the LangChain wrapper test is then skipped.

## Files

- `tools/sqlite_readonly.py` — securely opens SQLite `mode=ro`; checks real schema; validates a single `SELECT` statement; restricts authorizer to the correct table; caps displayed rows; formats natural-language summaries.
- `tools/db_tools.py` — dynamically defines `InstitutionsDBTool`, `HospitalsDBTool`, `RestaurantsDBTool` as actual LangChain `StructuredTool`s with descriptions listing columns read from each live database.
- `scripts/step03_test_db_tools.py` — tests real DB tool invocations and prints outputs.
- `tests/test_step03_db_tools.py` — offline automated tests including protection against deletion, wrong-table queries, and invented medical columns.

## What this step does NOT do yet

- Step 3 does **not** use an LLM, cost any tokens or require API keys.
- Tools accept a SQL `SELECT` statement such as `SELECT COUNT(*) AS records FROM institutions` rather than a user question.
- **Step 4** will add the Tavily WebSearchTool and **Step 5** will connect the LLM/Agent to choose tools and create correct SQL from user questions. Agent integration should explicitly handle out-of-scope questions rather than invent nonexistent fields.

## Critical dataset caveats

- `institutions` contains mainly educational institutions, not every government organization.
- `hospitals` includes health offices and facilities. For the question “How many hospitals in Dhaka?” filter `type` to actual hospital categories rather than count all facility rows.
- `restaurants` includes some non-restaurants, and has only a free-text `address` rather than a verified `district` column. It has no cuisine column.
- `COUNT(*)` measures dataset rows (may include duplicates), not the verified total real-world entities.
- The query engine rejects unauthorized SQL and queries that name non-existent columns instead of inventing data.

## Official LangChain reference

- https://reference.langchain.com/python/langchain-core/tools/structured/StructuredTool/from_function
