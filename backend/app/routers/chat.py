"""
KSP Crime Analytics — Chat Router
===================================
The main conversational AI endpoint.
Handles natural language queries with conversation history support.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.ai.orchestrator import process_query

router = APIRouter(prefix="/api/chat", tags=["Chat / Conversational AI"])


# ============================================================
# Request / Response Schemas
# ============================================================

class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list[ChatMessage]] = None


class SourceCase(BaseModel):
    case_id: Optional[int] = None
    crime_no: Optional[str] = None
    district: Optional[str] = None
    crime_type: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None
    relevance_score: Optional[float] = None
    excerpt: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str                          # sql, vector, general
    source: str                          # text-to-sql, vector-search, general
    success: bool
    sql_query: Optional[str] = None      # Only for SQL queries
    source_cases: Optional[list[SourceCase]] = None   # Only for vector search
    timestamp: str


# ============================================================
# Endpoints
# ============================================================

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main conversational AI endpoint.

    Send a natural language question and receive an AI-generated response.
    The system automatically routes your query to the appropriate agent:

    - **Statistical/data queries** → Text-to-SQL (queries PostgreSQL directly)
    - **Similarity/pattern queries** → Vector RAG (searches case narratives)
    - **General questions** → Direct LLM response

    Include `conversation_history` for context-aware follow-up questions.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Convert history to dict format for the orchestrator
    history = None
    if request.conversation_history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]

    # Process the query through the orchestrator
    result = await process_query(
        question=request.message,
        conversation_history=history,
    )

    # Build response
    return ChatResponse(
        answer=result.get("answer", "I couldn't process your query."),
        intent=result.get("intent", "unknown"),
        source=result.get("source", "unknown"),
        success=result.get("success", False),
        sql_query=result.get("sql_query"),
        source_cases=[
            SourceCase(**sc) for sc in result.get("source_cases", [])
        ] if result.get("source_cases") else None,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/build-index")
async def build_index():
    """
    Manually trigger building/rebuilding the vector search index.
    This embeds all BriefFacts from the database into ChromaDB.
    Run this once after loading data, or after adding new cases.
    """
    from app.ai.vector_search import build_vector_index
    try:
        build_vector_index(force_rebuild=True)
        return {"status": "success", "message": "Vector index built successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build index: {str(e)}")
