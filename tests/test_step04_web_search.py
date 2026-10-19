"""Offline Step 4 tests — no real Tavily calls and no API key required."""

import json

import pytest

from tools.web_search_tool import normalize_search_results, _safe_http_url, MAX_SEARCH_RESULTS


class StubSearch:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.queries = []

    def invoke(self, input):
        self.queries.append(input)
        if self.error:
            raise self.error
        return self.response


def sample_response(n=1):
    return {
        "results": [
            {"title": f"Result {i}", "url": f"https://example.org/{i}",
             "content": "Bangladesh public health information."}
            for i in range(n)
        ]
    }


def test_sources_and_excerpt_present():
    text = normalize_search_results("What does DGHS do?", sample_response(1))
    assert "https://example.org/0" in text
    assert "Bangladesh public health" in text
    assert "source excerpts" in text


def test_limits_result_count_and_snippet_size():
    results = sample_response(12)
    results["results"][0]["content"] = "x" * 8000
    text = normalize_search_results("Bangladesh", results)
    assert text.count("URL: ") == MAX_SEARCH_RESULTS
    assert "https://example.org/11" not in text
    assert len(text) < 5000


def test_does_not_claim_answer_without_real_sources():
    assert "Do not guess" in normalize_search_results("query", {"results": []})
    assert "Do not guess" in normalize_search_results("query", {"answer": "unsupported"})
    assert "unexpected" in normalize_search_results("query", None)


def test_rejects_non_http_source_links():
    assert _safe_http_url("file:///etc/passwd") is None
    assert _safe_http_url("javascript:alert(1)") is None
    assert _safe_http_url("https://user:pass@example.org/") is None
    assert _safe_http_url("https://example.org/test") == "https://example.org/test"
    assert "Do not guess" in normalize_search_results(
        "query", {"results": [{"url": "javascript:alert(1)", "content": "bad"}]}
    )


def test_json_string_works_and_plain_string_not_treated_as_evidence():
    assert "https://example.org/0" in normalize_search_results("query", json.dumps(sample_response()))
    assert "No factual answer" in normalize_search_results("query", "hello world")


def test_web_tool_uses_langchain_structuredtool(monkeypatch):
    pytest.importorskip("langchain_core")
    from tools.web_search_tool import build_web_search_tool

    backend = StubSearch(sample_response())
    tool = build_web_search_tool(search_client=backend)
    assert tool.name == "WebSearchTool"
    assert "query" in tool.args
    answer = tool.invoke({"query": "  What does DGHS do?  "})
    assert "https://example.org/0" in answer
    assert backend.queries == [{"query": "What does DGHS do?"}]
    assert tool.invoke({"query": "  "}).startswith("Web search rejected:")
    assert len(backend.queries) == 1
    assert tool.invoke({"query": "x" * 501}).startswith("Web search rejected:")
    assert len(backend.queries) == 1


def test_web_tool_hides_exception_details():
    pytest.importorskip("langchain_core")
    from tools.web_search_tool import build_web_search_tool

    backend = StubSearch(error=RuntimeError("API_KEY_WOULD_BE_SECRET"))
    result = build_web_search_tool(search_client=backend).invoke({"query": "test query"})
    assert "Web search unavailable" in result
    assert "API_KEY_WOULD_BE_SECRET" not in result


def test_all_four_tools_with_temporary_databases(tmp_path):
    pytest.importorskip("langchain_core")
    import sqlite3
    from tools.all_tools import build_all_tools

    dbdir = tmp_path / "databases"
    dbdir.mkdir()
    for table in ("institutions", "hospitals", "restaurants"):
        with sqlite3.connect(dbdir / f"{table}.db") as conn:
            conn.execute(f"CREATE TABLE {table} (name TEXT, district TEXT)")
            conn.execute(f"INSERT INTO {table} VALUES ('Example', 'Dhaka')")
    tools = build_all_tools(tmp_path, search_client=StubSearch(sample_response()))
    assert {tool.name for tool in tools} == {
        "InstitutionsDBTool", "HospitalsDBTool", "RestaurantsDBTool", "WebSearchTool",
    }
    assert "records = 1" in tools[0].invoke({"sql": "SELECT COUNT(*) AS records FROM institutions"})
    assert "https://example.org/0" in tools[3].invoke({"query": "role of DGHS"})
