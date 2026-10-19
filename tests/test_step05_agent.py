"""Step 5 offline tests: no OpenAI/Tavily credentials, no network use."""
from __future__ import annotations
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("langchain_classic")

from agent.main_agent import ask_agent, build_main_agent, create_prompt, SYSTEM_PROMPT
from agent.offline_demo_llm import MockTavilySearch, ScriptedOfflineChatModel


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    dbdir = tmp_path / "databases"
    dbdir.mkdir()
    for table in ("institutions", "hospitals", "restaurants"):
        with sqlite3.connect(dbdir / f"{table}.db") as conn:
            conn.execute(f'CREATE TABLE {table} (name TEXT, district TEXT, type TEXT, address TEXT)')
            conn.execute(f"INSERT INTO {table} (name, district, type, address) VALUES (?, ?, ?, ?)",
                         (f"Example {table}", "Dhaka", "Hospital" if table == "hospitals" else "Other", "Dhaka"))
    return tmp_path


@pytest.mark.parametrize("tool_name,sql", [
    ("InstitutionsDBTool", "SELECT COUNT(*) AS total FROM institutions"),
    ("HospitalsDBTool", "SELECT COUNT(*) AS total FROM hospitals"),
    ("RestaurantsDBTool", "SELECT COUNT(*) AS total FROM restaurants"),
])
def test_mocked_agent_executor_invokes_selected_database(sample_project, tool_name, sql):
    model = ScriptedOfflineChatModel(planned_tool=tool_name, planned_args={"sql": sql})
    executor = build_main_agent(sample_project, llm=model, search_client=MockTavilySearch())
    answer = ask_agent(executor, "How many records exist?")
    assert answer["used_tools"] == [tool_name]
    assert "total = 1" in answer["answer"]
    assert answer["source_urls"] == []
    assert "OFFLINE DEMO ONLY" in answer["answer"]


def test_mocked_web_tool_trace_and_source(sample_project):
    model = ScriptedOfflineChatModel(planned_tool="WebSearchTool", planned_args={"query": "DGHS Bangladesh"})
    executor = build_main_agent(sample_project, llm=model, search_client=MockTavilySearch())
    result = ask_agent(executor, "What is DGHS?")
    assert result["used_tools"] == ["WebSearchTool"]
    assert result["source_urls"] == ["https://example.org/offline-demo-only"]
    assert "OFFLINE DEMO ONLY" in result["answer"]


def test_missing_question_is_rejected(sample_project):
    llm = ScriptedOfflineChatModel(planned_tool="InstitutionsDBTool", planned_args={"sql": "SELECT COUNT(*) FROM institutions"})
    executor = build_main_agent(sample_project, llm=llm, search_client=MockTavilySearch())
    with pytest.raises(ValueError, match="empty"):
        ask_agent(executor, "  ")
    with pytest.raises(ValueError, match="long"):
        ask_agent(executor, "A" * 3001)


def test_prompt_contains_required_scratchpad_and_routing():
    prompt = create_prompt()
    assert "agent_scratchpad" in prompt.input_variables
    for name in ("InstitutionsDBTool", "HospitalsDBTool", "RestaurantsDBTool", "WebSearchTool"):
        assert name in SYSTEM_PROMPT
    assert "do NOT" in SYSTEM_PROMPT or "Do not" in SYSTEM_PROMPT


def test_missing_live_groq_key_fails_early(sample_project, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        build_main_agent(sample_project, search_client=MockTavilySearch())


def test_uses_exactly_four_tools(sample_project):
    llm = ScriptedOfflineChatModel(planned_tool="InstitutionsDBTool", planned_args={"sql": "SELECT COUNT(*) FROM institutions"})
    executor = build_main_agent(sample_project, llm=llm, search_client=MockTavilySearch())
    assert {t.name for t in executor.tools} == {
        "InstitutionsDBTool", "HospitalsDBTool", "RestaurantsDBTool", "WebSearchTool"
    }
