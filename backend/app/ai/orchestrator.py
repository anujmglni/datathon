"""
KSP Crime Analytics — Query Orchestrator
==========================================
Routes incoming natural language queries to the appropriate AI agent:
  - Text-to-SQL Agent → for structured/statistical questions
  - Vector Search Agent → for semantic/similarity questions
  - General Chat → for greetings, explanations, or general AI knowledge

Uses keyword heuristics + LLM classification for routing.
This is a lightweight alternative to a full LangGraph setup,
optimized for speed at a datathon.
"""

import re
from app.ai import llm as llm_module   # noqa: F401 — triggers Settings init
from app.ai.text_to_sql import query_sql
from app.ai.vector_search import query_vector

# ============================================================
# INTENT CLASSIFICATION
# ============================================================

# Keywords that strongly suggest a SQL/structured query
SQL_KEYWORDS = [
    "how many", "count", "total", "number of", "list all", "show me",
    "which district", "top", "most", "least", "maximum", "minimum",
    "average", "between", "last year", "last month", "this year",
    "registered", "cases in", "crimes in", "fir", "cases from",
    "status", "charge sheet", "arrest", "heinous", "accused in",
    "victims in", "station", "police station", "trend", "per month",
    "per year", "per district", "breakdown", "distribution",
    "gender", "age group", "category", "gravity",
]

# Keywords that strongly suggest a semantic/similarity search
VECTOR_KEYWORDS = [
    "similar", "like this", "modus operandi", "pattern", "resembl",
    "related cases", "find cases where", "incidents involving",
    "cases about", "describe", "narrative", "story", "summary",
    "brief facts", "what happened", "tell me about",
    "roof", "knife", "gun", "weapon", "vehicle", "fraud",
    "cyber", "drug", "gang", "robbery", "burglary",
    "money trail", "financial", "suspicious", "network",
]

# General chat / greeting patterns
GENERAL_PATTERNS = [
    r"^(hi|hello|hey|namaste|good\s*(morning|afternoon|evening))",
    r"^(who are you|what can you do|help|what is this)",
    r"^(thank|thanks|bye|exit|quit)",
    r"^(explain|what is|define|meaning of)",
]


def classify_intent(question: str) -> str:
    """
    Classify the user's question into one of three intents:
    - 'sql'     → Structured data query (use Text-to-SQL)
    - 'vector'  → Semantic similarity search (use RAG Vector Search)
    - 'general' → General conversation (use direct LLM)
    """
    q_lower = question.lower().strip()

    # Check general patterns first
    for pattern in GENERAL_PATTERNS:
        if re.match(pattern, q_lower):
            return "general"

    # Score SQL vs Vector keywords
    sql_score = sum(1 for kw in SQL_KEYWORDS if kw in q_lower)
    vector_score = sum(1 for kw in VECTOR_KEYWORDS if kw in q_lower)

    if sql_score > vector_score:
        return "sql"
    elif vector_score > sql_score:
        return "vector"
    elif sql_score > 0:
        return "sql"    # Default to SQL if tied
    else:
        return "vector"  # Default to vector for ambiguous queries


# ============================================================
# GENERAL CHAT HANDLER
# ============================================================

async def handle_general(question: str) -> dict:
    """Handle greetings and general questions using the LLM directly."""
    from llama_index.llms.ollama import Ollama

    llm = Ollama(
        model="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.7,
        request_timeout=60.0,
    )

    system_prompt = """You are the KSP Crime Analytics Assistant, an AI-powered tool
for the Karnataka State Police. You help investigators, analysts, and policymakers
query the state crime database using natural language.

You can:
1. Answer statistical questions about crimes (e.g., "How many theft cases in Bangalore?")
2. Find cases with similar patterns or modus operandi
3. Identify repeat offenders and criminal networks
4. Provide crime trend analysis and hotspot identification

Be professional, concise, and helpful. If the user asks a data question,
guide them to rephrase it as a specific query."""

    try:
        response = llm.complete(f"{system_prompt}\n\nUser: {question}\nAssistant:")
        return {
            "success": True,
            "answer": str(response),
            "source": "general",
        }
    except Exception as e:
        return {
            "success": True,
            "answer": (
                "👋 Namaste! I am the KSP Crime Analytics Assistant. I can help you:\n\n"
                "📊 **Query crime data** — \"How many murder cases in Bangalore this year?\"\n"
                "🔍 **Find similar cases** — \"Find cases involving robbery with a knife\"\n"
                "👤 **Identify repeat offenders** — \"Show repeat offenders in Mysuru\"\n"
                "📈 **Analyze trends** — \"Crime trend in Belagavi for the last 12 months\"\n\n"
                "What would you like to know?"
            ),
            "source": "general",
        }


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

async def process_query(question: str, conversation_history: list[dict] = None) -> dict:
    """
    Main entry point for processing a user's natural language query.
    Routes to the appropriate agent based on intent classification.

    Args:
        question: The user's natural language question
        conversation_history: Previous messages for context (optional)

    Returns:
        dict with keys: success, answer, source, and agent-specific metadata
    """
    # Classify intent
    intent = classify_intent(question)

    # Add context from conversation history if available
    if conversation_history and len(conversation_history) > 0:
        # Append recent context to help the agent
        recent_context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-4:]   # Last 4 messages
        ])
        enhanced_question = f"Previous conversation:\n{recent_context}\n\nCurrent question: {question}"
    else:
        enhanced_question = question

    # Route to the appropriate agent
    if intent == "sql":
        result = await query_sql(enhanced_question)
    elif intent == "vector":
        result = await query_vector(enhanced_question)
    else:
        result = await handle_general(question)

    # Attach routing metadata
    result["intent"] = intent
    result["original_question"] = question

    return result
