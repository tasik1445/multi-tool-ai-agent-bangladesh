# 🇧🇩 Multi-Tool AI Agent for Bangladesh

An assignment project that answers questions about **Bangladesh institutions, healthcare facilities, and food places** from three **SQLite databases**, and delegates **general-knowledge / policy questions** to a **Tavily web search** tool.

Built with **Python, LangChain Classic AgentExecutor, Groq tool-calling LLM, SQLite, Tavily, and Streamlit**.

> **Data scope:** Dataset rows are not official current national totals. The hospitals source includes non-hospital health offices, and the restaurants source includes non-restaurant places. The source data does not have explicit hospital-bed/doctor counts or cuisine categories. Do not infer missing facts.

## Architecture

```text
User question (Bangla / English)
            |
            v
Streamlit UI (app.py)  /  terminal CLI (scripts/step05_chat.py)
            |
            v
LangChain AgentExecutor + Groq (openai/gpt-oss-20b)
            |
   tool calling/routing
            |
    +-------+-----------+-------------+--------------+
    |                   |             |              |
InstitutionsDBTool HospitalsDBTool RestaurantsDBTool WebSearchTool
    |                   |             |              |
institutions.db     hospitals.db   restaurants.db  Tavily API
    |                   |             |              |
    +-------------------+-------------+--------------+
            |
            v
Answer + observed tool names + source URLs (when web searched)
```

The SQL tools accept **read-only SQLite SELECT** statements, use actual column names in their descriptions, and reject writes. The agent uses returned evidence rather than hard-coded counts. The UI presents **tools actually invoked**, based on AgentExecutor intermediate steps, not merely self-reported tool names.

## Dataset attribution

Original datasets by [Mahadih534 on Hugging Face](https://huggingface.co/Mahadih534/datasets):

1. [Institutional Information of Bangladesh](https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh)
2. [All Bangladeshi Hospitals](https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals)
3. [Bangladeshi Restaurant Data](https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data)

Review each dataset card's license and attribution conditions before redistributing underlying CSV/SQLite copies. Generated CSV files and `.db` files are **not tracked in this repository by default**; they can be reconstructed with the script below. This keeps the code submission reproducible without committing data files or API keys.

### Observed dataset counts

Counts observed when initially built (subject to source updates):

| SQLite file | Table | Example imported rows | Scope |
|---|---|---:|---|
| `databases/institutions.db` | `institutions` | 34,901 | Mostly educational institution records |
| `databases/hospitals.db` | `hospitals` | 38,886 | Health facilities/offices, **not only hospitals** |
| `databases/restaurants.db` | `restaurants` | 12,703 | Food/place records, **not only restaurants** |

The Streamlit sidebar reads current row counts from your **actual local databases**, rather than assuming the example numbers above.

## Repository layout

```text
Multi_Tool_AI_Agent_Bangladesh/
├── agent/
│   ├── __init__.py
│   ├── main_agent.py                  # Groq + AgentExecutor + prompts + routing
│   └── offline_demo_llm.py            # Scripted mock model for offline testing
├── tools/
│   ├── __init__.py
│   ├── sqlite_readonly.py             # Secured read-only SQL
│   ├── db_tools.py                    # 3 DB-specific LangChain tools
│   ├── web_search_tool.py             # Tavily web search
│   └── all_tools.py                   # Combines 4 tools
├── scripts/
│   ├── step02_build_databases.py
│   ├── step02_verify_databases.py
│   ├── step03_test_db_tools.py
│   ├── step04_test_web_search.py
│   ├── step05_check_groq.py
│   ├── step05_test_agent.py
│   └── step05_chat.py
├── tests/                              # Unit/integration tests from Steps 2–6
├── data/                               # Generated data is ignored by Git
├── databases/                          # Generated SQLite files are ignored by Git
├── app.py                              # Streamlit interface
├── ui_helpers.py                       # UI history/source/database helpers
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup: Windows + VS Code (Python 3.12 recommended)

1. Clone or open the project root in VS Code and open **Terminal > New Terminal**.
2. Create a virtual environment and install dependencies:

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activating the environment, **in the current terminal only**:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

3. In the root folder, create `.env` from the example:

```powershell
Copy-Item .env.example .env
code .env
```

Edit it to contain your actual keys:

```dotenv
GROQ_API_KEY=gsk_YOUR_GROQ_KEY
GROQ_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=YOUR_TAVILY_KEY
```

Never commit `.env`. [Get a Groq key](https://console.groq.com/keys) and [get a Tavily key](https://app.tavily.com/). Provider free-tier availability and limits may change.

4. Build the three SQLite databases (internet needed the first time):

```powershell
python scripts/step02_build_databases.py
python scripts/step02_verify_databases.py
```

5. Run automated **offline** tests (no LLM/web API calls):

```powershell
python -m pytest -q
```

6. Optional API/agent checks (they may consume Groq/Tavily free-tier quota):

```powershell
python scripts/step05_check_groq.py --ping
python scripts/step05_test_agent.py --live
```

7. Start the chatbot:

```powershell
python -m streamlit run app.py
```

Open the **Local URL** from the terminal, normally `http://localhost:8501`. Stop the server with `Ctrl+C`.

Alternatively, use the terminal chatbot:

```powershell
python scripts/step05_chat.py
```

## Example questions

| Example question | Expected tool type |
|---|---|
| How many institution records are in the dataset? | `InstitutionsDBTool` |
| Which institution types occur in Dhaka district? | `InstitutionsDBTool` |
| How many health-facility records are in Dhaka district? | `HospitalsDBTool` |
| List 5 well-rated food places with at least 20 reviews. | `RestaurantsDBTool` |
| What is the role of DGHS in Bangladesh? Cite sources. | `WebSearchTool` |
| বাংলাদেশের কোন জেলায় সবচেয়ে বেশি শিক্ষাপ্রতিষ্ঠান রয়েছে? | `InstitutionsDBTool` |

The model may use multiple tools for mixed questions. For hospital *counts*, it must distinguish unfiltered health-facility rows from actual hospital-type records; for the latter, check the `type` field.

## Tests and evidence

- Step 2: dataset acquisition, typed SQLite conversion, row/schema verification.
- Step 3: read-only SQL enforcement, invalid SQL rejection, per-database isolation.
- Step 4: Tavily response normalization, source URLs, error paths.
- Step 5: scripted offline tool-calling tests plus a **separate** live Groq/Tavily test; the latter is **not** part of pytest to avoid unexpected quota usage.
- Step 6: pure helper tests for chat history, safe URL filtering, secret-safe errors, and live local SQLite row counters.

The original project developer reported **11/11 Step 5 automated tests passed**, and observed actual tool calls for all four tools. These are historical local verification results, not a claim about every other environment. Test Step 6 on the target Windows PC before submitting.

## Safety, accuracy, and scope

- SQL tools run against SQLite in read-only mode. They do **not** execute writes.
- API keys are loaded from `.env`, which is ignored by Git; the UI does not print secrets.
- The assistant should not invent missing schema columns or data. Sources returned by Tavily may be incomplete or stale; prefer official primary sources for Bangladesh policy claims.
- No guarantees are made about live hospital capacities, bed availability, opening hours, restaurant reservations, or restaurant cuisine.
- Streamlit chat history is **session-only**. Recent completed question/answer pairs are forwarded to Groq for conversational continuity; do not enter sensitive personal information.
- The UI is a **local assignment demo**, not a hardened public service. Do not expose it on the public internet without authentication, abuse prevention, and additional safeguards.

## GitHub submission (after successful local UI test)

Create a new **empty** repository on GitHub (do not initialize it with a separate README), then in the project root:

```powershell
git init
git add .
git status
```

**Before continuing**, confirm `git status` does **not** list `.env`, `.venv/`, or source raw CSVs. Only then run:

```powershell
git commit -m "Build Bangladesh multi-tool LangChain agent with Streamlit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

If Git is not configured, set your own local Git identity first (`git config user.name` and `git config user.email`). Replace the placeholder GitHub URL with your repository URL. If the origin already exists, do not add it again; check `git remote -v`.

### Submission checklist

- [ ] Working `app.py` demo (screenshot showing a DB question and a web question)
- [ ] README and Python source in GitHub
- [ ] `requirements.txt`, `.env.example` and `.gitignore`
- [ ] Three database build/verify scripts and four actual tool implementations
- [ ] Offline tests and live-routing demo run locally
- [ ] GitHub URL submitted; optional Colab demo if desired

## Technical references

- [LangChain Classic AgentExecutor](https://reference.langchain.com/python/langchain-classic/agents/agent/AgentExecutor)
- [Groq model catalog](https://console.groq.com/docs/models)
- [Groq API limits](https://console.groq.com/docs/rate-limits)
- [Streamlit chat elements](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input)
- [SQLite Python API](https://docs.python.org/3/library/sqlite3.html)
