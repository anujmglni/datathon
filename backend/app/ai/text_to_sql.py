"""
KSP Crime Analytics — Text-to-SQL Agent
========================================
Converts natural language questions into SQL queries against the
PostgreSQL crime database using LlamaIndex's NLSQLTableQueryEngine.

Examples:
    "How many murder cases were registered in Bangalore last year?"
    "Show me top 5 districts by crime count"
    "List all accused in case number 202600001"
"""

from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from sqlalchemy import create_engine

from app.config import settings

# Sync engine for LlamaIndex (it doesn't support async SQLAlchemy yet)
_sync_engine = create_engine(settings.sync_database_url, echo=False)

# ============================================================
# SQL Database — Expose schema to the LLM
# ============================================================
# We include the most important tables for querying.
# The LLM will see the column names, types, and sample rows.

INCLUDED_TABLES = [
    "casemaster",
    "victim",
    "accused",
    "complainantdetails",
    "arrestsurrender",
    "actsectionassociation",
    "chargesheetdetails",
    "crimehead",
    "crimesubhead",
    "casestatusmaster",
    "gravityoffence",
    "casecategory",
    "district",
    "unit",
    "employee",
    "court",
    "act",
    "section",
    "inv_occurancetime",
]

sql_database = SQLDatabase(
    _sync_engine,
    include_tables=INCLUDED_TABLES,
    sample_rows_in_table_info=3,   # Show 3 sample rows per table to the LLM
)

# ============================================================
# Text-to-SQL Query Engine
# ============================================================

SYSTEM_PROMPT = """You are a SQL expert working with the Karnataka State Police (KSP) crime database.
The database contains FIR (First Information Report) records, victim details, accused persons,
arrest records, and crime classifications for Karnataka, India.

IMPORTANT RULES:
1. ALWAYS use PostgreSQL syntax.
2. Table and column names are ALL LOWERCASE in the database.
3. The central table is 'casemaster' which links to all other tables.
4. 'crimeno' is the unique FIR number, 'caseno' is the case serial number.
5. Use JOINs to resolve IDs to names (e.g., join 'district' to get district names).
6. For crime types, join 'crimesubhead' (specific type) and 'crimehead' (category).
7. For case status, join 'casestatusmaster'.
8. 'brieffacts' column contains the case summary text.
9. LIMIT results to 20 rows unless the user asks for more.
10. When counting, always use COUNT(*) with appropriate GROUP BY.
11. For date filtering, 'crimeregistereddate' is the FIR registration date.
12. Latitude and longitude are in 'casemaster' for location-based queries.

When you generate SQL, make sure it is correct and executable PostgreSQL."""


def get_sql_query_engine() -> NLSQLTableQueryEngine:
    """Create and return a Text-to-SQL query engine."""
    return NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=INCLUDED_TABLES,
        verbose=True,
        synthesize_response=True,
        sql_only=False,
    )


async def query_sql(question: str) -> dict:
    """
    Execute a natural language query against the crime database.
    Returns the SQL query generated, raw results, and a natural language response.
    """
    engine = get_sql_query_engine()

    # Prepend context to the question
    enhanced_question = f"{SYSTEM_PROMPT}\n\nUser Question: {question}"

    try:
        response = engine.query(enhanced_question)

        # Extract the generated SQL from metadata
        sql_query = response.metadata.get("sql_query", "N/A") if response.metadata else "N/A"
        result_rows = response.metadata.get("result", []) if response.metadata else []

        return {
            "success": True,
            "answer": str(response),
            "sql_query": sql_query,
            "result_rows": result_rows[:20],   # Cap at 20 rows for response
            "source": "text-to-sql",
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"I couldn't generate a valid SQL query for that question. Error: {str(e)}",
            "sql_query": None,
            "result_rows": [],
            "source": "text-to-sql",
        }
