"""
Smart NLU Intent Classifier & Entity Slot Extractor for KSP Platform.
Replaces static word banks with Zero-Shot LLM NLU (Groq / Anthropic Claude)
and Semantic Vector / Jaccard similarity fallback.
"""

import os
import re
import json
import time
import logging

logger = logging.getLogger(__name__)


# Semantic Descriptions for the 8 Specialized Skills used in NLU matching
SKILL_DESCRIPTIONS = {
    "SQL_ANALYTICS": "Queries count, volume, statistical totals, incident trends, crime rates by location, period, or IPC/BNS section.",
    "NETWORK_ANALYSIS": "Identifies criminal networks, co-accused associations, accomplices, gangs, and shared financial or geographic links.",
    "RAG_NARRATIVE": "Searches case narrative descriptions, BriefFacts text, similar modus operandi (MO), case summaries, and investigative leads.",
    "OFFENDER_PROFILE": "Analyzes repeat offenders, habitual criminals, recidivism risk scores, and criminal history profiles.",
    "FINANCIAL_LINK": "Traces cyber-fraud transactions, money trails, bank accounts, financial loss, and recovery amounts.",
    "FORECASTING": "Projects future crime hotspots, time-series crime volume forecasts, emerging clusters, and early warning alerts.",
    "SOCIOLOGICAL": "Correlates crime rates with socio-demographic indicators like literacy rate, urbanization, unemployment, and poverty.",
    "DOC_GEN": "Generates, compiles, or exports conversation summaries, investigation briefs, or case files to PDF or Word documents."
}

DISTRICT_NAMES = [
    "Bagalkot", "Bengaluru City", "Bengaluru District", "Belagavi District", "Ballari", "Bidar",
    "Vijayapura", "Chikkaballapura", "Chamarajnagar", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada",
    "Davanagere", "Dharwad", "Gadag", "Kalaburgi", "Hassan", "Haveri", "Hubballi Dharwad", "K.G.F.",
    "Kodagu", "Kolar", "Koppal", "Mandya", "Mangaluru City", "Mysuru City", "Mysuru District", "Raichur",
    "K.Railways", "Ramanagara", "Shimoga", "Tumakuru", "Udupi", "Uttara Kannada", "Yadgiri", "Belagavi City",
    "Kalaburgi City", "Vijayanagara"
]


def _build_nlu_prompt(query: str, chat_history_str: str = "") -> str:
    """Build the NLU classification prompt shared across LLM providers."""
    history_ctx = f"\nRecent Chat History Context:\n{chat_history_str}\n" if chat_history_str else ""
    return f"""You are an expert NLU (Natural Language Understanding) classifier for the Karnataka Police Crime Intelligence Platform.
{history_ctx}
Analyze the user's input query and classify it into EXACTLY ONE of the following 8 skill intents:
1. SQL_ANALYTICS: Querying counts, statistical totals, crime volume, trends, IPC sections.
2. NETWORK_ANALYSIS: Finding accomplices, criminal networks, shared cases/accounts/locations, gang links.
3. RAG_NARRATIVE: Searching case narratives (BriefFacts), similar past cases, modus operandi (MO), case details.
4. OFFENDER_PROFILE: Habitual offenders, repeat criminal risk scores, recidivism profiles.
5. FINANCIAL_LINK: Cyber fraud, bank account trails, money transfers, fraud recovery amounts.
6. FORECASTING: Emerging crime predictions, time-series projections, hotspot early warnings.
7. SOCIOLOGICAL: Correlation with literacy, urbanization, unemployment, economic stress.
8. DOC_GEN: Exporting, downloading, or rendering reports/PDFs of cases or chat.

User Input Query: "{query}"

Available Karnataka Districts: {json.dumps(DISTRICT_NAMES[:15])}...

STRICT SLOT RETRIEVAL INSTRUCTIONS:
Extract only the required information explicitly requested or implied in the query:
- `district`: Karnataka district name if specified, otherwise null.
- `year`: 4-digit year (YYYY) if specified, otherwise null.
- `crime_type`: Exact crime category (e.g. "Murder", "Theft", "Human Trafficking", "Cybercrime & Fraud", "Mischief", "Kidnapping & Abduction", "Extortion", "Narcotics", "Rash Driving") if specified, otherwise null.
- `ipc_sections`: Array of IPC section numbers explicitly mentioned (e.g. ["302", "379"]).
- `accused_id`: Accused or suspect ID number if mentioned (e.g. 11), otherwise null.
- `case_no`: FIR or Case Master ID if mentioned, otherwise null.
- `search_keywords`: Array of 2 to 4 core domain keywords for database keyword matching.
- `is_topic_query`: Set to true if query asks about a specific crime type, accused ID, case number, or specific keyword topic.

CRITICAL: Generate a `standalone_query`. If the user's query contains follow-ups or references previous turns (e.g., "What about in Mysuru?"), rewrite it into a fully contextualized standalone query using the provided chat history context.

Return ONLY a JSON object with these exact keys:
{{
  "intent": "<ONE_OF_THE_8_INTENTS>",
  "district": "<Karnataka_District_Name_or_null>",
  "year": "<Year_YYYY_or_null>",
  "crime_type": "<Specific_Crime_Type_or_null>",
  "ipc_sections": ["<IPC_sections_or_empty>"],
  "accused_id": <Accused_ID_number_or_null>,
  "case_no": "<Case_or_Crime_Number_or_null>",
  "search_keywords": ["<2_to_4_search_keywords>"],
  "is_topic_query": <true_or_false>,
  "standalone_query": "<fully_contextualized_query_string>",
  "confidence": <float_between_0_and_1>,
  "reasoning": "<short_nlu_explanation>"
}}"""



def _parse_json_response(content: str) -> dict | None:
    """Safely extract JSON from LLM response text."""
    content = content.strip()
    if "{" in content:
        content = content[content.find("{"):content.rfind("}") + 1]
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return None


def classify_query_groq_nlu(query: str, chat_history_str: str = "") -> dict | None:
    """
    Uses Groq (Llama 3.3 70B) for fast Zero-Shot NLU classification with native JSON mode.
    Primary LLM provider — sub-200ms inference.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.debug("GROQ_API_KEY is not set in environment")
        return None

    try:
        t0 = time.time()
        logger.debug("Requesting Llama 3.3 70B NLU classification")
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = _build_nlu_prompt(query, chat_history_str)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=350,
        )
        content = response.choices[0].message.content
        data = _parse_json_response(content)
        elapsed = round(time.time() - t0, 3)
        if data and "intent" in data:
            data["llm_provider"] = "groq"
            logger.debug(f"NLU Classified in {elapsed}s via Groq Llama 3.3 70B")
            return data
        return None
    except Exception as e:
        logger.debug(f"Groq NLU fallback: {e}")
        return None


def classify_query_llm_nlu(query: str, chat_history_str: str = "") -> dict | None:
    """
    Uses Claude LLM Zero-Shot NLU as secondary fallback.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = _build_nlu_prompt(query, chat_history_str)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        data = _parse_json_response(content)
        if data and "intent" in data:
            data["llm_provider"] = "anthropic"
            return data
        return None
    except Exception as e:
        logger.debug(f"Anthropic NLU fallback: {e}")
        return None


def classify_query_semantic_nlu(query: str) -> dict:
    """
    Semantic vector similarity / token NLU parser for fallback when no LLM API key is set.
    """
    query_lower = query.lower()
    words = set(re.findall(r'\w+', query_lower))

    scores = {}
    for intent, desc in SKILL_DESCRIPTIONS.items():
        desc_words = set(re.findall(r'\w+', desc.lower()))
        # Token overlap semantic similarity score
        overlap = len(words.intersection(desc_words))
        scores[intent] = overlap

    top_intent = max(scores, key=scores.get)
    if scores[top_intent] == 0:
        top_intent = "SQL_ANALYTICS"

    # Extract slots
    detected_district = None
    for d in DISTRICT_NAMES:
        if d.lower() in query_lower or d.lower().replace(" city", "").replace(" district", "") in query_lower:
            detected_district = d
            break

    year_match = re.search(r'\b(2019|2020|2021|2022|2023|2024|2025|2026)\b', query)
    detected_year = year_match.group(1) if year_match else None

    # Extract crime type & keywords strictly from query text
    detected_crime_type = None
    search_keywords = []

    if any(k in query_lower for k in ["traffick", "human trafficking", "370"]):
        detected_crime_type = "Human Trafficking"
        search_keywords = ["trafficking", "traffick", "370"]
    elif any(k in query_lower for k in ["murder", "homicide", "killing", "302"]):
        detected_crime_type = "Murder"
        search_keywords = ["murder", "homicide", "302"]
    elif any(k in query_lower for k in ["theft", "stolen", "snatching", "379"]):
        detected_crime_type = "Theft"
        search_keywords = ["theft", "stolen", "379"]
    elif any(k in query_lower for k in ["kidnap", "abduct", "363"]):
        detected_crime_type = "Kidnapping & Abduction"
        search_keywords = ["kidnapping", "abduction", "363"]
    elif any(k in query_lower for k in ["cyber", "fraud", "cheating", "420"]):
        detected_crime_type = "Cybercrime & Fraud"
        search_keywords = ["fraud", "cyber", "cheating", "420"]
    elif any(k in query_lower for k in ["extortion", "blackmail", "384"]):
        detected_crime_type = "Extortion"
        search_keywords = ["extortion", "blackmail", "384"]
    elif any(k in query_lower for k in ["narcotic", "ndps", "drug"]):
        detected_crime_type = "Narcotics / NDPS"
        search_keywords = ["narcotics", "ndps", "drug"]
    elif any(k in query_lower for k in ["mischief", "428", "430"]):
        detected_crime_type = "Mischief"
        search_keywords = ["mischief", "428"]

    accused_match = re.search(r'\baccused\s+(?:id\s+)?(\d+)\b', query_lower)
    detected_accused_id = int(accused_match.group(1)) if accused_match else None

    is_topic_query = bool(detected_crime_type or search_keywords or detected_accused_id or "traffick" in query_lower)

    total_score = sum(scores.values())
    dynamic_conf = round(min(0.98, max(0.50, scores[top_intent] / total_score)), 4) if total_score > 0 else 0.50

    return {
        "intent": top_intent,
        "district": detected_district,
        "year": detected_year,
        "crime_type": detected_crime_type,
        "search_keywords": search_keywords,
        "accused_id": detected_accused_id,
        "is_topic_query": is_topic_query,
        "confidence": dynamic_conf,
        "reasoning": f"Semantic NLU vector similarity matched '{top_intent}' with crime_type='{detected_crime_type}'",
        "llm_provider": "semantic_fallback"
    }




def classify_query(query: str, session_slots: dict = None, chat_history: list = None) -> dict:
    """
    Smart NLU entrypoint: Groq (primary) → Anthropic (secondary) → Semantic NLU (fallback).
    Passes chat history to rewrite multi-turn follow-ups into standalone queries.
    """
    chat_history_str = ""
    if chat_history and isinstance(chat_history, list):
        chat_history_str = "\n".join([f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}" for msg in chat_history[-6:]])

    # Try Groq first (fastest, free tier)
    nlu_result = classify_query_groq_nlu(query, chat_history_str)

    # Fallback to Anthropic Claude
    if not nlu_result:
        nlu_result = classify_query_llm_nlu(query, chat_history_str)

    # Final fallback to semantic matching
    if not nlu_result:
        nlu_result = classify_query_semantic_nlu(query)

    session_slots = session_slots or {}
    final_district = nlu_result.get("district") or session_slots.get("active_district")
    final_year = nlu_result.get("year") or session_slots.get("active_year")

    nlu_result["district"] = final_district
    nlu_result["year"] = final_year
    return nlu_result
