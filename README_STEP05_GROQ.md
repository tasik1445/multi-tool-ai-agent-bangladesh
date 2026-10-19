# Step 5 — Free-tier Groq Migration Patch (Windows VS Code)

This PATCH updates ONLY the Step 5 LLM/provider and related scripts/tests. Preserve your three SQLite databases, database/web tools, Hugging Face data, and earlier Step 2–4 files. The underlying `AgentExecutor`, `create_tool_calling_agent`, and four tools remain unchanged. The patch does **not** contain or overwrite `.env`.

**Provider:** GroqCloud. The `openai/gpt-oss-20b` **model ID** describes an open-weight model HOSTED ON GROQ, not the paid OpenAI Platform API. Groq Free Plan has rate/token limits and availability depends on your account. Older tutorials recommending `llama-3.3-70b-versatile` as free are now obsolete.

## 1. Get free API key

Open https://console.groq.com/keys and create a GroqCloud API key. Don't post it, and keep it out of git. Groq rate limits: https://console.groq.com/docs/rate-limits

## 2. Extract ZIP into existing Windows project root

`D:\Multi_Tool_AI_Agent_Bangladesh`

Merge folders and **overwrite ONLY** these old Step 5 files:

- `agent/main_agent.py`
- `scripts/step05_test_agent.py`
- `scripts/step05_chat.py`
- `tests/test_step05_agent.py`

The ZIP also adds:
- `tests/test_step05_groq_switch.py`
- `scripts/step05_check_groq.py`
- `.env.groq.example`
- `requirements_groq.txt`
- this README.

Do NOT replace `tools/`, `databases/`, `data/` or your `.env`.

## 3. Install package

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
.\.venv\Scripts\Activate.ps1
python -m pip install -U langchain-groq langchain-classic langchain-tavily python-dotenv pytest
```

## 4. Configure the existing `.env`

```dotenv
GROQ_API_KEY=gsk_YOUR_REAL_KEY_GOES_HERE
GROQ_MODEL=openai/gpt-oss-20b
TAVILY_API_KEY=YOUR_EXISTING_REAL_TAVILY_KEY
```

The previous `OPENAI_API_KEY` is **not used**. You may remove it from `.env` if you like. Do NOT remove `.env` from `.gitignore`.

## 5. Run sequentially

```powershell
python scripts/step05_check_groq.py
python scripts/step05_check_groq.py --ping
python -m pytest -q tests/test_step05_agent.py tests/test_step05_groq_switch.py
python scripts/step05_test_agent.py
python scripts/step05_test_agent.py --live
python scripts/step05_chat.py
```

- `step05_check_groq.py`: local key presence only (no network).
- `--ping`: ONE REAL Groq model call to ensure account/model access. Uses provider quota.
- pytest: scripted mock tool + model tests; does not prove live routing.
- default test_agent.py: mock LLM and mock Tavily, but real SQLite files.
- `--live`: real model + DB + Tavily; validates observed tools and source URLs.
- chat.py: interactive real agent.

No response is considered verified just because the model says it called a tool: live smoke test reads `intermediate_steps`.

## Common troubleshooting

- `GROQ_API_KEY is missing`: check `.env` at the project root; run the check script.
- `model_decommissioned` / `model_permission` / `not_found`: confirm available models in Groq console. Another model with tool-use support listed on Free Plan: `openai/gpt-oss-120b` (set `GROQ_MODEL=openai/gpt-oss-120b`).
- `RateLimitError` / HTTP 429: wait for Groq's token/request limit to reset, then retry fewer times; daily quota may take longer. No retry loop is included.
- Web source missing: check Tavily quota, `TAVILY_API_KEY`, and network; Tavily can have its own usage limits.
- `ModuleNotFoundError: langchain_groq`: run package install with your project venv activated.
- `No module named ...` for tools: ensure ZIP was extracted INTO the existing project directory without an extra nested folder.

## References

- Groq model catalog: https://console.groq.com/docs/models
- Groq free limits: https://console.groq.com/docs/rate-limits
- LangChain ChatGroq: https://reference.langchain.com/python/langchain-groq/chat_models/ChatGroq
- LangChain classic AgentExecutor: https://reference.langchain.com/python/langchain-classic/agents/agent/AgentExecutor
