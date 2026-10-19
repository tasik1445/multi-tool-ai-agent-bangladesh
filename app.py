"""Step 6: Streamlit chatbot for the verified Step 5 AgentExecutor.

Run from the project root: python -m streamlit run app.py
Never store secrets in this file or in Streamlit session state.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from ui_helpers import (
    completed_turns,
    database_counts,
    safe_error_message,
    validated_sources,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT / ".env", override=False)

st.set_page_config(
    page_title="Bangladesh Multi-Tool AI Agent",
    page_icon="🇧🇩",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Connecting to Groq and loading four tools...")
def get_executor():
    """One reusable AgentExecutor per Streamlit server process.

    Conversation histories remain *per browser session*; they are NOT saved
    on the cached shared executor. The four tools execute read-only queries.
    """
    from agent.main_agent import build_main_agent
    return build_main_agent(ROOT, verbose=False)


def render_assistant(message: dict) -> None:
    st.markdown(message["content"])
    tools = message.get("tools", [])
    if tools:
        st.caption("Tools actually called: " + ", ".join(tools))
    else:
        st.caption("No tool call recorded for this response")
    sources = validated_sources(message.get("sources", []))
    if sources:
        with st.expander(f"Web sources ({len(sources)})"):
            for index, url in enumerate(sources, 1):
                st.link_button(f"Source {index}: {url.split('/')[2]}", url)


if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

with st.sidebar:
    st.header("🇧🇩 Bangladesh AI Agent")
    st.caption("Groq LLM · LangChain AgentExecutor · SQLite · Tavily")
    st.markdown("**Active LLM**")
    st.code(os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), language=None)
    st.markdown("**Local dataset records**")
    counts = database_counts(ROOT)
    for label, key in (
        ("Educational institutions", "institutions"),
        ("Health facility records", "hospitals"),
        ("Food-place records", "restaurants"),
    ):
        count = counts[key]
        st.write(f"{label}: **{count:,}**" if count is not None else f"{label}: ⚠️ DB missing")
    st.caption("These are source dataset rows, not verified national totals.")
    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()
    st.caption("The current session keeps chat history locally in memory. No chat database is created.")
    st.caption("Web answers depend on retrieved source quality. Free-tier API limits apply.")

st.title("🇧🇩 Bangladesh Multi-Tool AI Assistant")
st.write("Ask in **Bangla or English** about institutions, hospitals, restaurants, or general Bangladesh knowledge.")
st.caption("Database questions → read-only SQLite tools | General knowledge → Tavily web search")

if any(count is None for count in counts.values()):
    st.error("One or more SQLite databases are missing or unreadable. Run: python scripts/step02_build_databases.py")
    st.stop()

examples = [
    ("Institutions", "How many institution records are in the dataset?"),
    ("Hospitals", "How many health-facility records are in Dhaka district?"),
    ("Restaurants", "Show 5 highly rated food places in Dhaka with at least 20 reviews."),
    ("Web search", "What is the role of DGHS in Bangladesh? Cite a source."),
]

st.markdown("**Try an example**")
example_cols = st.columns(4)
example_question = None
for index, (title, sample) in enumerate(examples):
    with example_cols[index]:
        if st.button(title, use_container_width=True, key=f"sample_{index}"):
            example_question = sample

for item in st.session_state.chat_messages:
    with st.chat_message(item["role"]):
        if item["role"] == "assistant":
            render_assistant(item)
        else:
            st.markdown(item["content"])

typed_question = st.chat_input("Ask about Bangladesh in Bangla or English...", max_chars=3000)
question = example_question or typed_question
if question:
    # Previous completed turns only; do not include the current query twice.
    pairs = completed_turns(st.session_state.chat_messages, max_pairs=4)
    chat_history = []
    for user_text, bot_text in pairs:
        chat_history.extend([HumanMessage(content=user_text), AIMessage(content=bot_text)])

    question = question.strip()
    st.session_state.chat_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("The agent is selecting and running the right tools..."):
                from agent.main_agent import ask_agent
                response = ask_agent(get_executor(), question, chat_history=chat_history)
        except Exception as exc:
            # We never display the raw exception, which might contain secrets.
            st.error(safe_error_message(exc))
            st.info("Your question was not added to chat history. You can retry it.")
            st.session_state.chat_messages.pop()
        else:
            record = {
                "role": "assistant",
                "content": response["answer"],
                "tools": list(response.get("used_tools", [])),
                "sources": validated_sources(response.get("source_urls", [])),
            }
            st.session_state.chat_messages.append(record)
            render_assistant(record)
