"""Smoke test. Offline default = scripted fake model; --live uses real API."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.main_agent import ask_agent, build_main_agent
from agent.offline_demo_llm import MockTavilySearch, ScriptedOfflineChatModel


OFFLINE_CASES = [
    ("institutions", "How many institution records are in this dataset?", "InstitutionsDBTool",
     {"sql": "SELECT COUNT(*) AS total FROM institutions"}),
    ("hospitals", "How many health-facility records are in this dataset?", "HospitalsDBTool",
     {"sql": "SELECT COUNT(*) AS total FROM hospitals"}),
    ("restaurants", "How many food-place records are in this dataset?", "RestaurantsDBTool",
     {"sql": "SELECT COUNT(*) AS total FROM restaurants"}),
    ("web", "What does DGHS mean?", "WebSearchTool", {"query": "What does DGHS mean?"}),
]


def test_offline() -> int:
    print("OFFLINE: scripted mock LLM + synthetic web search. No intelligent routing or live API use.\n")
    for label, question, tool_name, tool_args in OFFLINE_CASES:
        llm = ScriptedOfflineChatModel(planned_tool=tool_name, planned_args=tool_args)
        executor = build_main_agent(ROOT, llm=llm, search_client=MockTavilySearch())
        result = ask_agent(executor, question)
        print(f"[{label}] Used tools: {result['used_tools']}")
        print("Result:", result["answer"].splitlines()[0][:240])
        assert result["used_tools"] == [tool_name], f"Expected {tool_name}, got {result['used_tools']}"
    print("\nSTEP 5 OFFLINE PASS — 4 AgentExecutor tool integrations verified with scripted test calls.")
    return 0


def test_live() -> int:
    print("LIVE: Groq free-tier tool-calling LLM + Tavily. Subject to provider API quotas.\n")
    executor = build_main_agent(ROOT)
    checks = [
        ("How many institution records are in the provided institutions dataset?", "InstitutionsDBTool"),
        ("What is the role of DGHS in Bangladesh? Cite a source.", "WebSearchTool"),
    ]
    for question, expected_tool in checks:
        print("QUESTION:", question)
        result = ask_agent(executor, question)
        print("ANSWER:", result["answer"])
        print("TOOLS ACTUALLY CALLED:", ", ".join(result["used_tools"]) or "NONE")
        if result["source_urls"]:
            print("SOURCES:", *result["source_urls"], sep="\n - ")
        print()
        if expected_tool not in result["used_tools"]:
            print("LIVE ROUTING CHECK FAILED: expected tool was not used.")
            return 1
        if expected_tool == "WebSearchTool" and not result["source_urls"]:
            print("LIVE SOURCE CHECK FAILED: no Tavily sources were returned; check Tavily credentials/results.")
            return 1
    print("STEP 5 LIVE PASS — DB and Web tool routing were observed with real API calls.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use Groq and Tavily APIs (subject to free-plan limits)")
    args = parser.parse_args()
    try:
        return test_live() if args.live else test_offline()
    except (RuntimeError, FileNotFoundError, ValueError, ImportError) as exc:
        # Runtime setup errors are safe and helpful to print; no API token is read back here.
        print("SETUP ERROR:", str(exc))
        return 1
    except Exception as exc:
        # Network/provider exceptions sometimes carry HTTP headers or credentials.
        print(f"AGENT ERROR: {type(exc).__name__}. Check Groq/Tavily API keys, free-tier rate limits, model access, and network.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
