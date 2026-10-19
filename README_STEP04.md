# Step 4 — Tavily WebSearchTool Integration

This is an **incremental patch** for the Windows + VS Code project from Steps 1–3. Do **not** delete your previous `databases/`, `data/`, `.venv/`, `tools/db_tools.py`, or `tools/sqlite_readonly.py` files.

## 1. Merge this ZIP into your existing folder

Unzip and copy `tools/`, `scripts/`, `tests/` folders into:

`D:\Multi_Tool_AI_Agent_Bangladesh`

Merge folders; retain all existing files. Two files under `tools/` are new (`web_search_tool.py` and `all_tools.py`).

## 2. Activate Python and install dependency

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
.\.venv\Scripts\Activate.ps1
python -m pip install -U langchain-tavily python-dotenv
```

## 3. Configure Tavily key for real web searches

Get a Tavily API key at https://app.tavily.com/ . Then:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
code .env
```

Set `TAVILY_API_KEY=your_actual_key` in `.env`. It should not have placeholder text. Do **not** paste the actual key in ChatGPT, screenshots, GitHub or the source files. The existing `.gitignore` must contain `.env`.

**Important:** SQLite tools do not need any API key. Tavily is only needed for `--live` below. The `OPENAI_API_KEY` is not yet needed (Step 5).

## 4. Test offline first (no API usage)

```powershell
python -m pytest -q tests/test_step04_web_search.py
python scripts/step04_test_web_search.py
```

Expected: `8 passed` and `STEP 4 SUCCESSFUL — 4 tools verified (MOCK / OFFLINE mode).` If any test is skipped, check if the virtual environment has `langchain-core` installed.

Offline web results are **fake** and marked as DEMO ONLY; they are not real facts.

## 5. Test LIVE Tavily Web Search

```powershell
python scripts/step04_test_web_search.py --live
```

This makes **one real Tavily search API call** and can consume API credits. It searches for `What is the role of DGHS in Bangladesh?` and prints short source excerpts and real URLs. If it succeeds, you will see:

`STEP 4 SUCCESSFUL — 4 tools verified (LIVE API mode).`

If the live command reports missing key, ensure `.env` exists in project root and `TAVILY_API_KEY` is set. If it returns no source URLs, check internet connectivity, account quota and key validity. Never share the secret itself.

## Architecture

- `tools/web_search_tool.py`: `build_web_search_tool(...)` returns a LangChain `StructuredTool` called `WebSearchTool`. Uses modern `from langchain_tavily import TavilySearch` with small Basic searches, bounded text, sourced URL links and guarded errors.
- `tools/all_tools.py`: `build_all_tools(...)` combines previous three DB tools and new WebSearchTool, ready for the main Agent (Step 5).
- `scripts/step04_test_web_search.py`: one script to test four tools, offline mock by default or live with `--live`.
- `tests/test_step04_web_search.py`: 8 offline unit/integration tests that do not need the key.

## Scope and safety

- **Step 4 is a working tool integration, not the finished Main AI Agent.** Natural-language routing to tools and LLM-generated final answers come in Step 5.
- The web tool returns short **retrieved evidence**, not an independently verified answer. Final answers should cite URLs and check source quality/date.
- For dataset count/statistics questions, the main Agent must favor the three read-only SQLite tools. Current policies and general knowledge should use WebSearchTool. Mixed questions may need multiple tools.
- Raw search snippets are untrusted content. Do not follow instructions contained in web results.
- Never expose `.env` or API keys in public GitHub repositories. You can keep `.env.example` with empty placeholders for documentation.

Docs: https://reference.langchain.com/python/langchain-tavily/tavily_search/TavilySearch and https://github.com/tavily-ai/langchain-tavily
