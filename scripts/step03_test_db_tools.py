"""Run basic real-data smoke tests for all Step 3 LangChain tools (no API key)."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.db_tools import build_db_tools


SAMPLE_SQL = {
    "InstitutionsDBTool": [
        "SELECT COUNT(*) AS institution_records FROM institutions",
        "SELECT district, COUNT(*) AS records FROM institutions WHERE district IS NOT NULL GROUP BY district ORDER BY records DESC LIMIT 5",
    ],
    "HospitalsDBTool": [
        "SELECT COUNT(*) AS facility_records FROM hospitals",
        "SELECT type, COUNT(*) AS records FROM hospitals GROUP BY type ORDER BY records DESC LIMIT 5",
    ],
    "RestaurantsDBTool": [
        "SELECT COUNT(*) AS place_records FROM restaurants",
        "SELECT name, rating, number_of_reviews, address FROM restaurants WHERE rating > 0 ORDER BY rating DESC, number_of_reviews DESC LIMIT 5",
    ],
}


def main() -> None:
    print("STEP 3: Testing three LangChain database tools against real Step 2 SQLite files")
    tools = build_db_tools(PROJECT_ROOT)
    assert {t.name for t in tools} == set(SAMPLE_SQL)
    for tool in tools:
        print(f"\n========== {tool.name} ==========")
        for query in SAMPLE_SQL[tool.name]:
            print("SQL:", query)
            answer = tool.invoke({"sql": query})
            print("RESULT:\n", answer)
            if answer.startswith(("Query rejected:", "SQL error:")):
                raise RuntimeError(f"Unexpected failed query in {tool.name}: {answer}")
    print("\nSTEP 3 SUCCESSFUL — 3 LangChain database tools verified.")


if __name__ == "__main__":
    main()
