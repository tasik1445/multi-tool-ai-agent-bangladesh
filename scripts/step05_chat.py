"""Step 5 live terminal chatbot: `python scripts/step05_chat.py`."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage, HumanMessage
from agent.main_agent import ask_agent, build_main_agent


def main() -> int:
    try:
        executor = build_main_agent(ROOT)
    except (RuntimeError, FileNotFoundError, ImportError) as exc:
        print("SETUP ERROR:", str(exc))
        return 1
    print("Bangladesh Multi-Tool AI Agent — LIVE Groq + Tavily")
    print("Type /exit to quit, /clear to reset chat. Free-tier APIs have usage limits; repeated questions can trigger 429 errors.\n")
    history: list = []
    while True:
        try:
            question = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() in {"/exit", "exit", "quit"}:
            break
        if question.lower() == "/clear":
            history.clear()
            print("Conversation cleared.\n")
            continue
        if not question:
            continue
        try:
            response = ask_agent(executor, question, history)
        except ValueError as exc:
            print("INPUT ERROR:", exc)
            continue
        except Exception as exc:
            print(f"REQUEST ERROR: {type(exc).__name__}. Check network, rate limits, and your account settings.")
            continue
        print("\nAgent >", response["answer"])
        print("Tools used:", ", ".join(response["used_tools"]) or "none (not tool-verified)")
        if response["source_urls"]:
            print("Web sources:", *response["source_urls"], sep="\n - ")
        print()
        history.extend([HumanMessage(content=question), AIMessage(content=response["answer"])])
        # Keep only the most recent four question/answer turns in context.
        history = history[-8:]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
