"""Step 3 — three LangChain StructuredTool objects, one per SQLite DB.

These tools accept SQL SELECT statements. In Step 4, the LLM agent will turn
natural-language questions into SQL SELECTs and route them to the right tool.
"""

from __future__ import annotations

from pathlib import Path
from langchain_core.tools import StructuredTool

from .sqlite_readonly import DATABASES, ReadOnlySQLite


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_db_tools(project_root: Path = PROJECT_ROOT) -> list[StructuredTool]:
    """Build all three LangChain tools, reading the real Step 2 schemas."""
    generated = []
    for key, config in DATABASES.items():
        reader = ReadOnlySQLite(project_root, config)

        # Expose only a single `sql` input to the agent, not the private reader.
        def make_function(current_reader: ReadOnlySQLite):
            def run_sql(sql: str) -> str:
                """Run a SELECT query against this tool's database."""
                return current_reader.execute(sql)
            return run_sql

        description = (
            f"Use {config.tool_name} for: {config.scope}. "
            f"Database table: {config.table}. "
            f"Actual available columns: {reader.schema_description()}. "
            "Input must be ONE SQLite SELECT query on this table; use COUNT, WHERE, "
            "GROUP BY, ORDER BY and LIMIT as needed. For precise geographic counts, "
            "use structured district/division fields when available; restaurants "
            "have only a free-text address field. "
            "Do not invent columns or numerical values. "
            f"Dataset limitation: {config.caution} "
            "The returned text is evidence from the dataset, not an independently "
            "verified current fact."
        )
        generated.append(
            StructuredTool.from_function(
                func=make_function(reader),
                name=config.tool_name,
                description=description,
            )
        )
    return generated
