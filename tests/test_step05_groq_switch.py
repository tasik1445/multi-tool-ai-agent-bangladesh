"""Tests specific to the free-tier provider switch; no HTTP requests."""
import sys
import types
from pathlib import Path
import pytest

pytest.importorskip("langchain_classic")
from agent.main_agent import DEFAULT_MODEL, _live_model


def test_groq_is_free_plan_default():
    assert DEFAULT_MODEL == "openai/gpt-oss-20b"


def test_missing_key_fails_without_network(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        _live_model(tmp_path)


def test_groq_model_configuration_is_used(monkeypatch, tmp_path: Path):
    captured = {}

    class FakeChatGroq:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(sys.modules, "langchain_groq", types.SimpleNamespace(ChatGroq=FakeChatGroq))
    monkeypatch.setenv("GROQ_API_KEY", "TEST_ONLY_NOT_REAL")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    _live_model(tmp_path)
    assert captured["model"] == "openai/gpt-oss-120b"
    assert captured["max_retries"] == 0
