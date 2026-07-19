"""
Automated unit tests for KSP FastAPI backend (PostgreSQL database integration).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intent_classifier import classify_query
from agent.governance import apply_governance_rules
from services.graph_analysis import build_criminal_network
from database import get_connection, execute_query

def test_intent_classification():
    res1 = classify_query("Show total theft cases in Bengaluru in 2023")
    assert res1["intent"] == "SQL_ANALYTICS"
    assert res1["district"] == "Bengaluru City" or res1["district"] == "Bengaluru District"
    assert res1["year"] == "2023"

    res2 = classify_query("Find criminal network and accomplices of accused A1")
    assert res2["intent"] == "NETWORK_ANALYSIS"

    res3 = classify_query("Download PDF report of recent cases")
    assert res3["intent"] == "DOC_GEN"

def test_governance_redaction():
    sql = "SELECT ComplainantName, CasteID, ReligionID FROM ComplainantDetails WHERE ComplainantID = 1;"
    
    # Analyst role should mask sensitive columns
    sql_redacted, was_redacted = apply_governance_rules(sql, "Analyst")
    assert was_redacted is True
    assert "NULL AS CasteID" in sql_redacted or "NULL AS casteid" in sql_redacted

    # Investigator role should preserve columns
    sql_preserved, was_redacted_inv = apply_governance_rules(sql, "Investigator")
    assert was_redacted_inv is False

def test_database_and_graph():
    conn, db_type = get_connection()
    assert conn is not None
    assert db_type in ["postgresql", "sqlite"]

    graph = build_criminal_network()
    assert "total_nodes" in graph
    assert "total_edges" in graph
