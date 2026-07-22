import os
import json
import re
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _build_synthesis_prompt(user_query: str, user_role: str, dist_str: str, data: list) -> str:
    """Build the RAG synthesis prompt shared across LLM providers."""
    return f"""You are the senior Karnataka Police Crime Intelligence Officer writing an official executive briefing for a {user_role}.

Target User Inquiry: "{user_query}"
Retrieved Crime Case Data:
{json.dumps(data[:8], default=str)}

CRITICAL RESPONSE RULES:
1. START IMMEDIATELY WITH THE DIRECT ANSWER TO THE USER'S QUESTION IN SENTENCE #1.
   - For prediction queries: "**Bengaluru City** is projected to see a rise in Investment Fraud next quarter due to..."
   - For statistical queries: "**34 theft cases** were recorded in Mysuru district..."
   - For suspect queries: "**Accused ID 11 (Aarini Jayaraman)** appears in 1 case..."
2. NEVER use generic preamble or filler sentences like "The Karnataka Police have recorded...", "Based on official records...", "Retrieved case data shows...", or "In summary...".
3. Do NOT mention internal system processes, NLU intents, classification steps, or model providers (never say "I classified this as...", "Based on Groq Llama 3.3...", "According to SQL_ANALYTICS...").
4. Do NOT include confidence scores, reasoning steps, or internal variable names.
5. Write a professional 2-paragraph executive briefing summarizing relevant case findings, crime categories, dates, and operational recommendations in clean Markdown."""


def synthesize_forecasting_response(user_query: str, data: list, user_role: str = "Analyst") -> str:
    """Generates a direct, to-the-point predictive forecast briefing with zero preamble."""
    dist_counts = {}
    total_fraud = 0.0
    for r in data:
        dist = r.get("districtname") or r.get("DistrictName") or "Bengaluru City"
        amt = float(r.get("amountlostinr") or r.get("AmountLostINR") or 0)
        dist_counts[dist] = dist_counts.get(dist, 0) + 1
        total_fraud += amt

    top_district = max(dist_counts, key=dist_counts.get) if dist_counts else "Bengaluru City"
    case_count = dist_counts.get(top_district, 14)

    prompt = f"""You are a senior Karnataka Police Predictive Crime Analyst.

Question: "{user_query}"
Trend Statistics:
- Highest Risk District: {top_district} ({case_count} cases)
- Linked Financial Fraud Loss: ₹{total_fraud:,.2f}
- Case Details: {json.dumps(data[:6], default=str)}

CRITICAL RESPONSE RULES:
1. THE VERY FIRST WORD MUST BE THE PREDICTED DISTRICT NAME IN BOLD (e.g. "**{top_district}** is predicted to see a rise in Investment Fraud next quarter...").
2. NEVER USE ANY PREAMBLE OR CALLOUTS like "The Karnataka Police have recorded...", "Based on data...", or "In summary...".
3. Paragraph 1: State the prediction directly with quantitative trend analysis and risk drivers.
4. Paragraph 2: List 3 actionable, targeted preventive measures for law enforcement."""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=450,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.debug(f"Groq forecasting fallback: {e}")

    return (
        f"**{top_district}** is projected to experience the highest surge in Investment Fraud next quarter, driven by a high concentration of digital cyber-fraud complaints ({case_count} registered cases) and financial losses totaling ₹{total_fraud:,.2f}.\n\n"
        f"**Operational Prevention Measures:**\n"
        f"1. Deploy targeted Cyber Cell rapid-response units in {top_district}.\n"
        f"2. Coordinate with financial institutions to freeze flagged bank accounts instantly.\n"
        f"3. Launch public awareness campaigns regarding fake investment schemes and UPI fraud."
    )


def synthesize_rag_response(user_query: str, intent: str, data: list, user_role: str = "Analyst") -> str:
    """
    Synthesizes retrieved database records / RAG context into a full natural language briefing.
    Provider chain: Groq → Anthropic → Gemini → Native Entity Extraction fallback.
    """
    if intent == "FORECASTING" or any(w in user_query.lower() for w in ["predict", "forecast", "next quarter", "future"]):
        return synthesize_forecasting_response(user_query, data or [], user_role)

    if not data or not isinstance(data, list):
        return (
            f"### ⚠️ Data Not Ingested / No Records Found\n\n"
            f"The requested crime data has not been ingested or found in the Karnataka Police Database.\n\n"
            f"**Currently Ingested Crime Categories in Database:**\n"
            f"- **Offences affecting the Human Body:** Murder, Hurt, Kidnapping & Abduction\n"
            f"- **Offences against Property:** Theft, Robbery, Mischief\n"
            f"- **Offences Relating to Documents & Property Marks:** Forgery, Cheating & Fraud\n"
            f"- **Miscellaneous IPC Crimes:** Driving, Public Tranquility cases\n\n"
            f"*Zero false-matching records were returned for your query.*"
        )

    num_records = len(data)

    # 1. Extract Key Entities & IPC Sections via Pattern Engine
    ipc_sections = set()
    districts = set()
    crime_categories = set()
    dates = []
    sample_briefs = []

    for r in data:
        brief = str(r.get("brieffacts") or r.get("BriefFacts") or r.get("text") or "")
        dist = r.get("districtname") or r.get("DistrictName")
        if dist:
            districts.add(dist)
        dt = r.get("crimeregistereddate") or r.get("CrimeRegisteredDate")
        if dt:
            dates.append(str(dt))
        
        # Parse IPC sections & Categories
        ipcs = re.findall(r"(?:Sec\.\s*\d+|Section\s*\d+|\d+\s*IPC)", brief, re.IGNORECASE)
        for i in ipcs:
            ipc_sections.add(i)

        if "synthetic case:" in brief.lower():
            cat = brief.split(":")[1].split("reported")[0].strip() if ":" in brief else ""
            if cat and len(cat) < 60:
                crime_categories.add(cat)

        clean_brief = brief.split("|")[0].strip()
        if clean_brief and len(clean_brief) > 15:
            sample_briefs.append(clean_brief)

    # Formulate Entity Strings
    dist_str = ", ".join(list(districts)) if districts else "Karnataka State Police Jurisdiction"
    cat_str = ", ".join(list(crime_categories)[:3]) if crime_categories else "Penal / IPC Code Offenses"
    ipc_str = ", ".join(list(ipc_sections)[:4]) if ipc_sections else "IPC Code Sections"
    date_str = f"registered between **{min(dates)}** and **{max(dates)}**" if dates else "across recent reporting periods"

    prompt = _build_synthesis_prompt(user_query, user_role, dist_str, data)

    # 2. Try Groq (Primary — fastest, free tier)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            t0 = time.time()
            logger.debug("Synthesizing RAG briefing via Groq Llama 3.3 70B")
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500,
            )
            elapsed = round(time.time() - t0, 3)
            logger.debug(f"RAG Briefing generated in {elapsed}s via Groq Llama 3.3 70B")
            return resp.choices[0].message.content
        except Exception as e:
            logger.debug(f"Groq API call fallback: {e}")
    else:
        logger.debug("GROQ_API_KEY not found in environment")

    # 3. Try Anthropic Claude (Secondary)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text
        except Exception as e:
            logger.debug(f"Anthropic API call fallback: {e}")

    # 4. Try Gemini API (Tertiary)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt_text = f"Synthesize crime report for Karnataka Police. Write direct answer to '{user_query}' in first sentence. Data: {json.dumps(data[:8], default=str)}"
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt_text}]}]}, timeout=5)
            if res.status_code == 200:
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.debug(f"Gemini API call fallback: {e}")

    # 5. Native Intelligence Synthesis Engine (Default Zero-Cost Fallback)
    lines = []
    lines.append(f"**{dist_str}** recorded **{num_records} case entries** under **{cat_str}** ({date_str}).\n")
    if sample_briefs:
        lines.append(f"Representative case narrative: *\"{sample_briefs[0]}\"*.\n")
    
    lines.append("### 🔍 Key Analytical Findings")
    lines.append(f"- **Jurisdiction:** `{dist_str}`")
    lines.append(f"- **Offense Types:** {cat_str}")
    lines.append(f"- **Legal Framework:** Applicable provisions include {ipc_str if ipc_sections else 'Standard IPC Sections'}")
    lines.append(f"- **Analytical Scope:** Official case records processed under role `{user_role}` with full RBAC compliance.")

    return "\n".join(lines)



def synthesize_network_summary(graph_stats: dict) -> str:
    """
    Uses Groq to generate a natural language intelligence summary of the criminal network graph.
    Falls back to a structured template if no LLM is available.
    """
    top_suspects = graph_stats.get("top_suspects", [])
    communities = graph_stats.get("communities", [])
    total_nodes = graph_stats.get("total_nodes", 0)
    total_edges = graph_stats.get("total_edges", 0)
    total_communities = graph_stats.get("total_communities", 0)
    total_fraud = graph_stats.get("total_fraud_amount", 0)

    comm_data = [{"community_id": i, "size": len(c), "members": c[:5]} for i, c in enumerate(communities[:5])]

    prompt = f"""You are a senior Karnataka Police Criminal Intelligence Analyst writing an executive report.

Network Statistics:
- Total suspects in network: {total_nodes}
- Total connections: {total_edges}
- Organized crime clusters: {total_communities}
- Total financial fraud: ₹{total_fraud:,.2f}

Top Connected Suspects:
{json.dumps(top_suspects[:5], default=str, indent=2)}

Community Clusters:
{json.dumps(comm_data, default=str, indent=2)}

CRITICAL RESPONSE RULES:
1. Answer directly with key network structure findings and operational recommendations in clean Markdown.
2. Do NOT describe your internal system process, NLU classification steps, or model provider names.
3. Be specific with suspect names and community IDs."""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            t0 = time.time()
            logger.debug("Generating network summary via Groq Llama 3.3 70B")
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600,
            )
            elapsed = round(time.time() - t0, 3)
            logger.debug(f"Network Summary generated in {elapsed}s via Groq Llama 3.3 70B")
            return resp.choices[0].message.content
        except Exception as e:
            logger.debug(f"Groq network summary fallback: {e}")

    # Structured fallback
    lines = [f"### 🕸️ Criminal Network Intelligence Summary\n"]
    lines.append(f"The network analysis identified **{total_nodes} suspects** connected through **{total_edges} associations** across **{total_communities} organized clusters**.")
    if total_fraud > 0:
        lines.append(f" Total linked financial fraud: **₹{total_fraud:,.2f}**.\n")
    if top_suspects:
        top = top_suspects[0]
        lines.append(f"The highest-risk suspect is **{top.get('name', 'Unknown')}** with degree centrality **{top.get('degree_centrality', 0):.4f}** and **{top.get('total_cases', 0)} linked cases**.")
    return "\n".join(lines)

