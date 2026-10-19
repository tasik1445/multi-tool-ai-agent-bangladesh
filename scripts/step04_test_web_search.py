"""Manual Step 4 smoke test. Offline by default, --live calls Tavily API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.all_tools import build_all_tools


class DemoSearchClient:
    """Deterministic example results, NEVER actual web evidence."""

    def invoke(self, payload: dict):
        return {
            "query": payload["query"],
            "results": [
                {
                    "title": "DEMO ONLY — public health agency",
                    "url": "https://example.org/demo-only",
                    "content": "Synthetic placeholder, not factual research. Live Tavily mode retrieves real sources.",
                }
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify all four LangChain tools")
    parser.add_argument("--live", action="store_true", help="Actually call Tavily (consumes API credits)")
    args = parser.parse_args()

    try:
        tools = build_all_tools(ROOT, search_client=None if args.live else DemoSearchClient())
    except (ImportError, RuntimeError, FileNotFoundError) as exc:
        print(f"SETUP ERROR: {exc}")
        return 1

    by_name = {tool.name: tool for tool in tools}
    expected = {"InstitutionsDBTool", "HospitalsDBTool", "RestaurantsDBTool", "WebSearchTool"}
    if set(by_name) != expected:
        print(f"TOOL NAME ERROR: {sorted(by_name)}")
        return 1
    print("Available tools:", ", ".join(sorted(by_name)))

    for name, table in (
        ("InstitutionsDBTool", "institutions"),
        ("HospitalsDBTool", "hospitals"),
        ("RestaurantsDBTool", "restaurants"),
    ):
        answer = by_name[name].invoke({"sql": f"SELECT COUNT(*) AS records FROM {table}"})
        if "records = " not in answer:
            print(f"DB TEST FAILED — {name}: {answer}")
            return 1
        print(f"{name}:", answer.splitlines()[0][:160])

    print("\nWeb tool query: What is the role of DGHS in Bangladesh?")
    answer = by_name["WebSearchTool"].invoke({"query": "What is the role of DGHS in Bangladesh?"})
    print(answer)
    if "URL: https://" not in answer and "URL: http://" not in answer:
        print("\nWEB TEST FAILED — no source links; check Tavily credentials/connectivity.")
        return 1
    mode = "LIVE API" if args.live else "MOCK / OFFLINE"
    print(f"\nSTEP 4 SUCCESSFUL — 4 tools verified ({mode} mode).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
