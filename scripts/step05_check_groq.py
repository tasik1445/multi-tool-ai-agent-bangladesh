"""Check .env/Groq model config without displaying secret values.

Default mode makes NO API request. Add --ping for one paid/free-tier
Groq LLM call, which is subject to rate limits.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ping", action="store_true", help="Make one real Groq request")
    args = parser.parse_args()
    load_dotenv(dotenv_path=ROOT / ".env", override=False)
    groq = os.environ.get("GROQ_API_KEY", "").strip()
    tavily = os.environ.get("TAVILY_API_KEY", "").strip()
    print("Groq key configured:", bool(groq) and not groq.lower().startswith("your_"))
    print("Tavily key configured:", bool(tavily) and not tavily.lower().startswith("your_"))
    print("Groq model:", os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"))
    if not groq or groq.lower().startswith("your_"):
        print("Set GROQ_API_KEY inside project root .env; DO NOT paste it in chat.")
        return 1
    if args.ping:
        try:
            from agent.main_agent import _live_model
            msg = _live_model(ROOT).invoke("Reply with exactly OK")
            print("Groq API reachable. Short response:", str(msg.content)[:80])
        except Exception as exc:
            print("Groq API request failed:", type(exc).__name__, "- Check account model access/rate limit/network.")
            return 1
    else:
        print("No API call was made. Add --ping to verify live Groq access.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
