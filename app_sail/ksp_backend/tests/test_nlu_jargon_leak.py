"""
Automated regression test suite for KSP Crime Intelligence Platform.
Asserts that NO internal NLU jargon, confidence scores, reasoning steps, or model provider names
(Groq, Llama, Claude, Anthropic, NLU, intent, llm_provider, etc.) ever leak into user-facing response strings.
"""

import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from agent.session import get_session
from agent.intent_classifier import classify_query
from services.hybrid_retrieval import execute_hybrid_search
from agent.llm_synthesizer import synthesize_rag_response, synthesize_network_summary
from services.graph_analysis import build_criminal_network

BANNED_JARGON_SUBSTRINGS = [
    "intent",
    "confidence",
    "groq",
    "llama",
    "anthropic",
    "claude-3",
    "reasoning",
    "NLU",
    "intent_classified",
    "llm_provider",
    "standalone_query"
]



def test_no_jargon_leaks_in_responses():
    sample_queries = [
        ("SQL_ANALYTICS", "Show total theft cases in Bengaluru in 2022"),
        ("NETWORK_ANALYSIS", "Find criminal network and accomplices of accused ID 11"),
        ("RAG_NARRATIVE", "Search case narratives for rash driving incident"),
        ("FINANCIAL_LINK", "Show investment fraud transactions and money trails"),
        ("FORECASTING", "Project future crime hotspots and emerging crime clusters")
    ]

    session = get_session("test_jargon_regression")
    session.reset()

    for intent_category, query_text in sample_queries:
        # 1. Classify intent
        intent_data = classify_query(query_text, session.active_slots, session.history)
        query_for_search = intent_data.get("standalone_query") or query_text

        # 2. Construct minimal downstream slots (no internal debug fields)
        effective_intent = {
            "intent": intent_data.get("intent", "SQL_ANALYTICS"),
            "district": intent_data.get("district") or session.active_slots.get("active_district"),
            "year": intent_data.get("year") or session.active_slots.get("active_year"),
            "crime_type": intent_data.get("crime_type") or session.active_slots.get("active_crime_type"),
            "ipc_sections": intent_data.get("ipc_sections") or session.active_slots.get("active_ipc_sections") or [],
            "search_keywords": intent_data.get("search_keywords") or session.active_slots.get("active_search_keywords") or [],
            "standalone_query": query_for_search
        }

        # 3. Retrieve records
        rows, sql = execute_hybrid_search(effective_intent, query_for_search, top_k=5)

        # 4. Synthesize final user-facing response string
        if intent_category == "NETWORK_ANALYSIS":
            graph_stats = build_criminal_network()
            response_text = synthesize_network_summary(graph_stats)
        else:
            response_text = synthesize_rag_response(query_for_search, effective_intent["intent"], rows)

        # 5. Assert ZERO banned jargon leakage
        response_lower = response_text.lower()
        for banned_word in BANNED_JARGON_SUBSTRINGS:
            assert banned_word.lower() not in response_lower, (
                f"❌ REGRESSION FAILURE: Leaked internal jargon '{banned_word}' in response for query '{query_text}'!\n"
                f"Response text:\n{response_text}"
            )

        session.add_turn(query_text, response_text)
