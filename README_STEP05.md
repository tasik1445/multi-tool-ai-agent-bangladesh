# Step 5 — Main LangChain AI Agent (AgentExecutor)

This is an **incremental patch** for the Windows/VS Code project created in Steps 1–4. Keep all existing `databases/*.db`, `tools/*.py`, `.env`, datasets, and earlier tests. **Merge** the ZIP folders; do not replace the entire project directory.

## What's included

| File | Purpose |
|---|---|
| `agent/main_agent.py` | Real LLM-backed AgentExecutor, systematic source-aware prompt, routing and tool trace extraction |
| `agent/offline_demo_llm.py` | Test-only deterministic mock chat model/search response. Not actual AI. |
| `agent/__init__.py` | Python package marker |
| `scripts/step05_test_agent.py` | Offline smoke test (default) and `--live` API smoke test |
| `scripts/step05_chat.py` | Live terminal chatbot using all four tools |
| `tests/test_step05_agent.py` | Eight offline tests (parameterized cases) |

The **prior files must remain intact**: `tools/db_tools.py`, `tools/sqlite_readonly.py`, `tools/web_search_tool.py`, `tools/all_tools.py`, and 3 `.db` files.

## 1 — Merge files

Extract the ZIP, merge `agent`, `scripts`, and `tests` into:

`D:\Multi_Tool_AI_Agent_Bangladesh`

The ZIP contains **no API keys** and does not overwrite your databases.

## 2 — Install/check dependencies

Open VS Code PowerShell terminal:

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
.\.venv\Scripts\Activate.ps1
python -m pip install -U langchain-classic langchain-core langchain-openai langchain-tavily python-dotenv pytest
```

Recommended: Python 3.11+ (user has 3.12). `AgentExecutor` was moved to `langchain-classic` in LangChain's newer release series. The project uses `create_tool_calling_agent` and `ChatOpenAI`.

## 3 — First run: offline verification (NO API keys required)

```powershell
python -m pytest -q tests/test_step05_agent.py
python scripts/step05_test_agent.py
```

The first script executes synthetic databases inside pytest temporary folders. The second **reads your three real SQLite DBs** and uses a *scripted mock LLM* to issue four predetermined tool calls and a fake web result. Successful output should end with:

`STEP 5 OFFLINE PASS — 4 AgentExecutor tool integrations verified with scripted test calls.`

**Important:** An offline pass only proves wiring to LangChain tools; it does NOT verify that a real LLM independently chooses the right tool or that Tavily succeeds. Do not use `example.org` as a factual citation.

## 4 — Configure API credentials for real agent tests

Create/edit your existing project root `.env` (do not publish it):

```dotenv
OPENAI_API_KEY=YOUR_REAL_OPENAI_PLATFORM_API_KEY
TAVILY_API_KEY=YOUR_REAL_TAVILY_KEY
OPENAI_MODEL=gpt-4.1-mini
```

Get OpenAI API credentials from https://platform.openai.com/api-keys and Tavily credentials from https://app.tavily.com/ . A ChatGPT subscription **does not include** OpenAI API usage by default; check API project billing, model access and available credits. A supported alternative tool-calling model can be set via `OPENAI_MODEL`.

Make sure `.gitignore` contains:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
```

Do not paste keys in ChatGPT or screenshots.

## 5 — Live test (makes API requests)

```powershell
python scripts/step05_test_agent.py --live
```

This exercises two *actual* questions: (1) source dataset institution count routed to `InstitutionsDBTool`; (2) DGHS role routed to `WebSearchTool`. The script checks the **observed intermediate tool calls**, not just what the LLM claims to have done. It also checks a Tavily source URL was returned. Each question may use multiple OpenAI model calls, and web search can consume credits.

If the API call fails, check your .env, billing, API quota, model access, Internet connection and Tavily credits; do not share keys.

## 6 — Live interactive chatbot (terminal)

```powershell
python scripts/step05_chat.py
```

Try these questions:

- `How many institutions in the dataset are in Dhaka district?`
- `Show five public hospital-type facilities in Chattogram. State the dataset scope.`
- `Which five restaurant records have the highest ratings?`
- `What is the role of DGHS in Bangladesh? Provide sources.`
- `ঢাকা জেলার কতটি শিক্ষাপ্রতিষ্ঠানের রেকর্ড আছে?`

Type `/exit` to quit and `/clear` to clear chat history. The app shows **tools actually called**. For web searches it also prints URLs extracted from Tavily results. If the LLM bypasses tools it prints `none (not tool-verified)`.

## Architecture

```text
User question -> ChatOpenAI + AgentExecutor
                   |          |           |             |
                   v          v           v             v
             Institutions  Hospitals  Restaurants     WebSearch
                DB Tool      DB Tool     DB Tool       (Tavily)
                   |          |           |
            institutions.db hospitals.db restaurants.db
                   \__________ evidence ____________/
                                |
                         Natural-language answer
                           + actual tool trace
                           + web URLs
```

**Limitations:** The datasets are snapshots and don't prove current nationwide counts. Hospitals dataset includes non-hospital health offices; it doesn't have explicit doctor or bed columns. Restaurants data has no cuisine column. The agent is instructed not to invent absent columns. Tool selection and SQL by a real LLM can still be imperfect; inspect trace and output.

**Security:** SQLite tools from Step 3 permit only read-only SELECT queries with authorizer/time limits; retrieved data and web excerpts are untrusted. Keys must stay in `.env`. Do not use SQL counts as authoritative national statistics without qualifying dataset coverage.

## Reference docs

- LangChain classic agent: https://reference.langchain.com/python/langchain-classic/agents/tool_calling_agent/base/create_tool_calling_agent
- LangChain AgentExecutor: https://reference.langchain.com/python/langchain-classic/agents/agent/AgentExecutor
- LangChain OpenAI ChatOpenAI: https://docs.langchain.com/oss/python/integrations/chat/openai
- Tavily integration: https://reference.langchain.com/python/langchain-tavily/tavily_search/TavilySearch

**Next Step 6:** optional Streamlit UI, full project-level integration tests, `.gitignore`/README, GitHub submission. Step 5 itself fulfills Main Agent logic; it doesn't train a new machine-learning model.
