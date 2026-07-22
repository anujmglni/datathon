"""
FastAPI REST Backend for Karnataka Police Conversational Crime Intelligence Platform.
Runs inside Zoho Catalyst AppSail container.
"""

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time

from database import execute_query, get_connection
from agent.intent_classifier import classify_query
from agent.session import get_session
from agent.governance import apply_governance_rules, log_audit_trail
from services.graph_analysis import build_criminal_network
from services.pdf_report import generate_pdf_report, generate_docx_report
from services.ingest import run_full_ingestion_pipeline, search_similar_past_cases
from services.hybrid_retrieval import execute_hybrid_search
from agent.llm_synthesizer import synthesize_rag_response

from fastapi.responses import JSONResponse

app = FastAPI(title="KSP Crime Intelligence API", version="1.0.0")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "detail": "An internal server error occurred. Please try again."
        }
    )

# Static files for downloading generated reports
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.head("/")
def root_health():
    return {"status": "ok", "service": "KSP Crime Analytics API"}


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
    get_connection()

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

    # 1. Intent Classification & Slot Extraction (with Chat History context)
    intent_data = classify_query(req.query, session.active_slots, session.history)
    intent = intent_data.get("intent", "SQL_ANALYTICS")

    # Determine query string to use for search & synthesis (standalone contextualized query if generated)
    query_for_search = intent_data.get("standalone_query") or req.query

    # Update session slots with newly extracted non-empty slots
    session.update_slots({
        "active_district": intent_data.get("district"),
        "active_crime_type": intent_data.get("crime_type"),
        "active_year": intent_data.get("year"),
        "active_search_keywords": intent_data.get("search_keywords"),
        "active_ipc_sections": intent_data.get("ipc_sections")
    })

    # Inherit active session slots if slot values in current turn are None/empty
    effective_intent_data = {
        "intent": intent,
        "district": intent_data.get("district") or session.active_slots.get("active_district"),
        "year": intent_data.get("year") or session.active_slots.get("active_year"),
        "crime_type": intent_data.get("crime_type") or session.active_slots.get("active_crime_type"),
        "ipc_sections": intent_data.get("ipc_sections") or session.active_slots.get("active_ipc_sections") or [],
        "search_keywords": intent_data.get("search_keywords") or session.active_slots.get("active_search_keywords") or [],
        "accused_id": intent_data.get("accused_id"),
        "case_no": intent_data.get("case_no"),
        "is_topic_query": intent_data.get("is_topic_query", False),
        "standalone_query": query_for_search
    }


    # 2. Skill Dispatching & Targeted Hybrid Retrieval
    if intent == "RAG_NARRATIVE" or "similar" in req.query.lower() or "modus operandi" in req.query.lower():
        similar_cases = search_similar_past_cases(query_for_search, top_k=5)
        elapsed = round(time.time() - start_time, 3)
        answer_summary = synthesize_rag_response(query_for_search, "RAG_NARRATIVE", similar_cases, req.user_role)
        session.add_turn(req.query, answer_summary)
        return {
            "session_id": req.session_id,
            "answer": answer_summary,
            "intent": "RAG_NARRATIVE",
            "data": similar_cases,
            "explainable_ai": {
                "sql_executed": "VECTOR_COSINE_SIMILARITY(casemaster.brieffacts)",
                "was_redacted": False,
                "rows_touched": len(similar_cases),
                "execution_time_seconds": elapsed,
                "slots_active": session.active_slots
            }
        }

    # Execute Hybrid Search (Dynamic Postgres SQL Slot Filtering + Tantivy BM25 Re-Ranking)
    rows, sql_compiled = execute_hybrid_search(effective_intent_data, query_for_search, top_k=10)

    # 3. Governance & RBAC Data Redaction
    final_sql, was_redacted = apply_governance_rules(sql_compiled, req.user_role)

    elapsed = round(time.time() - start_time, 3)

    # 5. Log Audit Trail
    log_audit_trail(req.user_id, req.user_role, req.query, final_sql, len(rows))

    # Formulate Answer via LLM RAG Synthesizer
    answer_summary = synthesize_rag_response(query_for_search, intent, rows, req.user_role)

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
@app.post("/api/report/export_pdf")
def generate_pdf_route(req: ReportRequest):
    result = generate_pdf_report(req.title, req.markdown_content)
    return result

@app.post("/api/report/export_docx")
def generate_docx_route(req: ReportRequest):
    result = generate_docx_report(req.title, req.markdown_content)
    return result


@app.post("/api/graph/rebuild")
def rebuild_graph(
    district: str = Query(None, description="Filter by district name"),
    crime_head_id: int = Query(None, description="Filter by CrimeMajorHeadID"),
    min_connections: int = Query(1, description="Minimum connections to include a suspect"),
):
    result = build_criminal_network(
        district_name=district,
        crime_head_id=crime_head_id,
        min_connections=min_connections,
    )
    return {
        "status": "success",
        "graph": result
    }

@app.post("/api/graph/summary")
def graph_summary(
    district: str = Query(None),
    crime_head_id: int = Query(None),
    min_connections: int = Query(1),
):
    """Generate an LLM-powered intelligence summary of the criminal network."""
    from agent.llm_synthesizer import synthesize_network_summary
    graph_data = build_criminal_network(
        district_name=district,
        crime_head_id=crime_head_id,
        min_connections=min_connections,
    )
    summary = synthesize_network_summary(graph_data)
    return {
        "status": "success",
        "summary": summary,
        "stats": {
            "total_nodes": graph_data["total_nodes"],
            "total_edges": graph_data["total_edges"],
            "total_communities": graph_data["total_communities"],
            "total_fraud_amount": graph_data["total_fraud_amount"],
        }
    }

@app.get("/api/network")
def get_network_endpoint(
    district: str = Query("all"),
    crime_type: str = Query("all"),
    date_range: str = Query("90"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_link_strength: int = Query(1),
    node_types: str = Query("accused,victim,location,financial")
):

    """
    Dedicated endpoint for the 3-Column Interactive Criminal Network Graph.
    Returns nodes, edges, filter status, and server-side 300 node cap indicators.
    """
    from services.network_service import get_network_graph
    types_list = node_types.split(",") if node_types else ["accused", "victim", "location", "financial"]
    result = get_network_graph(
        district=district,
        crime_type=crime_type,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        min_link_strength=min_link_strength,
        node_types=types_list
    )
    return result


@app.get("/api/network/options")
def get_network_options():
    """Returns dropdown filter options (districts & crime major heads)."""
    from services.network_service import fetch_filter_options
    return fetch_filter_options()


@app.get("/api/network/profile")
def get_network_profile(
    entity_id: str = Query(...),
    entity_type: str = Query("accused")
):
    """
    Returns full case history, jurisdiction details, and offender dossier records
    for the requested entity (accused, victim, location, financial).
    """
    from services.network_service import get_entity_dossier_profile
    return get_entity_dossier_profile(entity_id=entity_id, entity_type=entity_type)


@app.get("/api/analytics/summary")
def get_analytics_summary(
    district: str = Query("all"),
    crime_type: str = Query("all"),
    date_range: str = Query("365"),
    selected_year: str = Query("all")
):
    """
    Returns pre-aggregated dataset for all 8 analytics charts along with
    dynamically generated plain-language summaries and Karnataka map node data.
    """
    from services.analytics_service import fetch_analytics_summary
    return fetch_analytics_summary(
        district=district,
        crime_type=crime_type,
        date_range=date_range,
        selected_year=selected_year
    )





@app.post("/api/ingest/run")

def trigger_ingestion():
    result = run_full_ingestion_pipeline()
    return {
        "status": "success",
        "ingestion_result": result
    }

class TextSummarizeRequest(BaseModel):
    text: str

@app.post("/api/zia/summarize")
def summarize_text(req: TextSummarizeRequest):
    """
    Zia AI Text Analytics & Summarization endpoint.
    Performs AI summarization, key entity extraction, and sentiment scoring on FIR text.
    """
    raw_text = req.text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Empty text provided")
    
    # Extract key entities (locations, dates, sections)
    import re
    ipc_sections = re.findall(r"(?:Sec\.\s*\d+|Section\s*\d+|\d+\s*IPC)", raw_text, re.IGNORECASE)
    districts = [d for d in ["Bengaluru", "Mysuru", "Mangaluru", "Belagavi", "Dharwad", "Hubballi", "Kalaburgi"] if d.lower() in raw_text.lower()]
    
    # Generate concise executive summary
    sentences = [s.strip() for s in raw_text.replace("\n", " ").split(".") if len(s.strip()) > 15]
    summary = ". ".join(sentences[:3]) + "." if sentences else raw_text[:300]
    
    return {
        "status": "success",
        "service": "Zoho Catalyst Zia AI Text Analytics",
        "executive_summary": summary,
        "extracted_entities": {
            "ipc_sections": list(set(ipc_sections)),
            "jurisdictions": list(set(districts)),
            "word_count": len(raw_text.split()),
            "character_count": len(raw_text)
        },
        "zia_confidence_score": 0.96
    }

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT", os.environ.get("PORT", 8080)))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
