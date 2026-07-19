"""
FastAPI REST Backend for Karnataka Police Conversational Crime Intelligence Platform.
Runs inside Zoho Catalyst AppSail container.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from database import execute_query, get_db_connection
from agent.intent_classifier import classify_query
from agent.session import get_session
from agent.governance import apply_governance_rules, log_audit_trail
from services.graph_analysis import build_criminal_network
from services.pdf_report import generate_pdf_report

app = FastAPI(title="KSP Crime Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    session_id: str | None = "default_session"
    user_role: str | None = "Analyst"
    user_id: str | None = "officer_101"

class ReportRequest(BaseModel):
    title: str
    markdown_content: str

@app.on_event("startup")
def startup_event():
    # Warm up database connection & populate local SQLite tables if needed
    get_db_connection()

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "catalyst_app_id": "45688000000013023",
        "timestamp": int(time.time())
    }

@app.post("/api/query")
def process_query(req: QueryRequest):
    start_time = time.time()
    session = get_session(req.session_id)

    # 1. Intent Classification & Slot Extraction
    intent_data = classify_query(req.query, session.active_slots)
    intent = intent_data["intent"]

    # Update session slots
    session.update_slots({
        "active_district": intent_data.get("district"),
        "active_year": intent_data.get("year")
    })

    # 2. Skill Dispatching & SQL Compilation
    sql_compiled = ""
    rows = []
    
    if intent_data.get("district"):
        sql_compiled = f"SELECT c.CrimeNo, c.CrimeRegisteredDate, c.BriefFacts, d.DistrictName FROM CaseMaster c JOIN District d ON c.PoliceStationID IN (SELECT UnitID FROM Unit WHERE DistrictID = d.DistrictID) WHERE d.DistrictName ILIKE '%{intent_data['district']}%' LIMIT 10;"
    else:
        sql_compiled = "SELECT CrimeNo, CrimeRegisteredDate, BriefFacts FROM CaseMaster ORDER BY CaseMasterID DESC LIMIT 10;"

    # 3. Governance & RBAC Data Redaction
    final_sql, was_redacted = apply_governance_rules(sql_compiled, req.user_role)

    # 4. Execute Query
    try:
        rows = execute_query(final_sql)
    except Exception as e:
        rows = [{"error": str(e)}]

    elapsed = round(time.time() - start_time, 3)

    # 5. Log Audit Trail
    log_audit_trail(req.user_id, req.user_role, req.query, final_sql, len(rows))

    # Formulate Answer
    answer_summary = f"Retrieved {len(rows)} cases targeting intent '{intent}'"
    if intent_data.get("district"):
        answer_summary += f" in jurisdiction '{intent_data['district']}'"
    if intent_data.get("year"):
        answer_summary += f" for year '{intent_data['year']}'"

    # Add to session history
    session.add_turn(req.query, answer_summary)

    return {
        "session_id": req.session_id,
        "answer": answer_summary,
        "intent": intent,
        "data": rows,
        "explainable_ai": {
            "sql_executed": final_sql,
            "was_redacted": was_redacted,
            "rows_touched": len(rows),
            "execution_time_seconds": elapsed,
            "slots_active": session.active_slots
        }
    }

@app.post("/api/report/generate")
def generate_report(req: ReportRequest):
    result = generate_pdf_report(req.title, req.markdown_content)
    return result

@app.post("/api/graph/rebuild")
def rebuild_graph():
    result = build_criminal_network()
    return {
        "status": "success",
        "graph": result
    }
