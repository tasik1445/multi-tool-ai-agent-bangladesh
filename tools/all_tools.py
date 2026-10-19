"""Step 4 — convenient assembly of the four LangChain tools for Step 5."""

from pathlib import Path
from typing import Any

from .db_tools import PROJECT_ROOT, build_db_tools
from .web_search_tool import build_web_search_tool


def build_all_tools(project_root: Path = PROJECT_ROOT, search_client: Any = None):
    """Return three preexisting read-only DB tools and the Tavily web tool."""
    tools = build_db_tools(project_root)
    tools.append(build_web_search_tool(project_root, search_client=search_client))
    return tools
