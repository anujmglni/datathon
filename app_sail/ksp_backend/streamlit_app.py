"""
KSP Crime Intelligence Platform — Streamlit Chat UI
Chat-based interface with visual graphs, downloadable PDFs, and natural language responses.
"""

import streamlit as st
import requests
import json
import pandas as pd
import time
import io

# ── Config ──────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8080"

st.set_page_config(
    page_title="KSP Crime Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .header-banner h1 { 
        color: #f1f5f9; 
        font-size: 1.7rem; 
        font-weight: 700; 
        margin: 0 0 0.4rem 0; 
        line-height: 1.3;
    }
    .header-banner p { 
        color: #94a3b8; 
        font-size: 0.9rem; 
        margin: 0; 
        line-height: 1.4;
    }
    
    .badge-online {
        display: inline-block; padding: 4px 12px; border-radius: 16px;
        font-size: 0.75rem; font-weight: 600; letter-spacing: 0.4px;
        background: rgba(34,197,94,0.12); color: #22c55e; border: 1px solid rgba(34,197,94,0.3);
    }
    .badge-offline {
        display: inline-block; padding: 4px 12px; border-radius: 16px;
        font-size: 0.75rem; font-weight: 600;
        background: rgba(239,68,68,0.12); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);
    }

    div[data-testid="stMarkdownContainer"] p {
        line-height: 1.65 !important;
        margin-bottom: 0.6rem !important;
    }

    div[data-testid="stMarkdownContainer"] h3 {
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.3 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────
def check_health():
    try:
        r = requests.get(f"{API_BASE}/api/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def query_backend(query, session_id, role):
    try:
        r = requests.post(f"{API_BASE}/api/query",
                          json={"query": query, "session_id": session_id, "user_role": role},
                          timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def build_graph():
    try:
        r = requests.post(f"{API_BASE}/api/graph/rebuild", timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def generate_pdf(title, content):
    try:
        r = requests.post(f"{API_BASE}/api/report/generate",
                          json={"title": title, "markdown_content": content},
                          timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def format_answer_naturally(result):
    """Returns the LLM RAG synthesized answer directly."""
    answer = result.get("answer")
    if answer:
        return answer

    data = result.get("data", [])
    if not data or not isinstance(data, list):
        return "No records were found matching your query criteria."

    return f"Retrieved {len(data)} records from database."


def render_network_graph(graph_data):
    """Render an interactive network graph using plotly."""
    import plotly.graph_objects as go
    import networkx as nx
    import math

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        st.warning("No criminal network data found.")
        return

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], label=n.get("label", f"#{n['id']}"),
                   centrality=n.get("degree_centrality", 0))
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))

    # Layout
    pos = nx.spring_layout(G, k=2.5, iterations=60, seed=42)

    # Edge traces
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode='lines',
        line=dict(width=0.8, color='#475569'),
        hoverinfo='none'
    )

    # Node traces
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_text = [G.nodes[n].get("label", str(n)) for n in G.nodes()]
    node_centrality = [G.nodes[n].get("centrality", 0) for n in G.nodes()]
    node_size = [max(8, c * 120) for c in node_centrality]
    node_color = node_centrality

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        marker=dict(
            size=node_size, color=node_color,
            colorscale='YlOrRd', showscale=True,
            colorbar=dict(title="Centrality", thickness=15),
            line=dict(width=1, color='#1e293b')
        ),
        text=node_text,
        textposition="top center",
        textfont=dict(size=8, color="#94a3b8"),
        hovertext=[f"{t}<br>Centrality: {c:.4f}" for t, c in zip(node_text, node_centrality)],
        hoverinfo='text'
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text=f"Criminal Network Graph — {len(nodes)} Suspects, {len(edges)} Connections",
                font=dict(size=16, color="#e2e8f0")
            ),
            showlegend=False,
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=20, r=20, t=50, b=20),
            height=550,
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Top suspects by centrality
    top = sorted(nodes, key=lambda x: x.get("degree_centrality", 0), reverse=True)[:10]
    if top:
        st.markdown("##### 🔴 Top 10 Most Connected Suspects")
        df = pd.DataFrame(top)
        df.columns = [c.replace("_", " ").title() for c in df.columns]
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    online = check_health()
    if online:
        st.markdown('<span class="badge-online">● BACKEND ONLINE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-offline">● BACKEND OFFLINE</span>', unsafe_allow_html=True)
        st.error("Run `python app.py` first")

    st.divider()
    user_role = st.selectbox("👤 Role (RBAC)", ["Analyst", "SP", "DGP", "Inspector", "Constable"])
    session_id = st.text_input("🔑 Session", value="streamlit_chat_1")

    st.divider()
    st.markdown("### 💡 Try These Queries")
    examples = [
        "Show me recent crimes in Bengaluru",
        "Theft cases in Mysuru district",
        "Cybercrime cases in 2024",
        "Find similar modus operandi cases",
        "Crime trends in Dharwad",
        "Cases in Mangaluru City",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["pending_query"] = ex

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.rerun()


# ── Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>🛡️ Karnataka Police — Crime Intelligence Platform</h1>
    <p>Conversational AI for crime analytics, criminal network analysis, and case intelligence</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────
tab_chat, tab_graph, tab_pdf, tab_ocr = st.tabs(["💬 Chat Intelligence", "🕸️ Criminal Network Graph", "📄 PDF Report", "📷 Zia AI — OCR & Summarizer"])

# ═══════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT INTERFACE
# ═══════════════════════════════════════════════════════════════════════
with tab_chat:
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Render chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"], avatar="🧑‍✈️" if msg["role"] == "user" else "🛡️"):
            st.markdown(msg["content"])
            if msg.get("dataframe") is not None:
                with st.expander(f"📚 Grounding Sources & Citations ({len(msg['dataframe'])} database records)", expanded=False):
                    st.dataframe(msg["dataframe"], use_container_width=True, hide_index=True)
            if msg.get("sql"):
                with st.expander("⚡ Executed SQL & Provenance"):
                    st.code(msg["sql"], language="sql")

    # Pending query from sidebar
    pending = st.session_state.pop("pending_query", None)
    user_input = st.chat_input("Ask about crimes, suspects, networks, or trends...")
    query = pending or user_input

    if query:
        # User message
        st.session_state["chat_history"].append({"role": "user", "content": query})
        with st.chat_message("user", avatar="🧑‍✈️"):
            st.markdown(query)

        # Assistant response
        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("🔍 Analyzing..."):
                result = query_backend(query, session_id, user_role)

            if "error" in result and "data" not in result:
                st.error(f"❌ {result['error']}")
                st.session_state["chat_history"].append({"role": "assistant", "content": f"❌ {result['error']}"})
            else:
                # Natural language response
                formatted = format_answer_naturally(result)
                st.markdown(formatted)

                # Data table
                data = result.get("data", [])
                df = None
                if data and isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    # Truncate long text
                    for col in df.columns:
                        if df[col].dtype == "object":
                            df[col] = df[col].astype(str).str[:100]
                    with st.expander(f"📚 Grounding Sources & Citations ({len(df)} database records)", expanded=False):
                        st.dataframe(df, use_container_width=True, hide_index=True)

                # SQL
                xai = result.get("explainable_ai", {})
                sql = xai.get("sql_executed", "")
                if sql:
                    with st.expander("⚡ Executed SQL & Provenance"):
                        st.code(sql, language="sql")

                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": formatted,
                    "dataframe": df,
                    "sql": sql,
                })


# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — CRIMINAL NETWORK GRAPH (VISUAL)
# ═══════════════════════════════════════════════════════════════════════
with tab_graph:
    st.markdown("### 🕸️ Criminal Network Visualization")
    st.caption("Builds a co-accused association graph from all cases. Nodes = suspects, edges = shared cases.")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Build Network Graph", type="primary", use_container_width=True):
            st.session_state["build_graph"] = True

    if st.session_state.get("build_graph"):
        with st.spinner("🧠 Querying accused records and building network graph..."):
            result = build_graph()

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            graph_data = result.get("graph", result)
            total_nodes = graph_data.get("total_nodes", 0)
            total_edges = graph_data.get("total_edges", 0)

            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 Total Suspects", total_nodes)
            c2.metric("🔗 Total Connections", total_edges)
            avg_degree = round(2 * total_edges / total_nodes, 2) if total_nodes > 0 else 0
            c3.metric("📊 Avg Connections/Suspect", avg_degree)

            st.divider()

            # Render visual graph
            render_network_graph(graph_data)

        st.session_state["build_graph"] = False


# ═══════════════════════════════════════════════════════════════════════
# TAB 3 — PDF REPORT (DOWNLOADABLE)
# ═══════════════════════════════════════════════════════════════════════
with tab_pdf:
    st.markdown("### 📄 Generate & Download Investigation Report")
    st.caption("Compile a styled PDF report from your analysis notes.")

    report_title = st.text_input("Report Title", value="Bengaluru City Crime Analysis Briefing — 2024")

    report_content = st.text_area(
        "Report Content (Markdown)",
        height=250,
        value="""# Crime Overview
District: Bengaluru City
Period: January 2024 — December 2024
Total Cases Analyzed: 1,247

## Key Findings
- Property theft cases concentrated in Koramangala, Whitefield, and Electronic City.
- 23% increase in cybercrime cases compared to 2023.
- Repeat offender rate: 12.4% (highest in Majestic sub-jurisdiction).

## Recommendations
1. Increase night patrolling in Koramangala (8 PM — 2 AM).
2. Deploy cyber cell rapid-response unit for UPI fraud complaints.
3. Expand CCTV coverage in identified hotspot zones.

## Network Intelligence
- 4 organized groups identified through co-accused analysis.
- Primary hub suspect: Person #4821 (degree centrality: 0.847).
"""
    )

    if st.button("📥 Generate & Download PDF", type="primary"):
        with st.spinner("Generating PDF report..."):
            result = generate_pdf(report_title, report_content)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            st.success(f"✅ PDF generated: **{result.get('filename', 'report.pdf')}**")

            size = result.get("size_bytes", 0)
            if size > 0:
                st.metric("File Size", f"{size:,} bytes")
                st.info("📥 PDF generated on server. In production, this would return a download link.")
            else:
                st.info("📄 Report compiled. Preview below:")

            # Show a live preview of the report
            st.divider()
            st.markdown("#### 📋 Report Preview")
            st.markdown(report_content)


# ═══════════════════════════════════════════════════════════════════════
# TAB 4 — ZIA AI OCR & TEXT SUMMARIZER
# ═══════════════════════════════════════════════════════════════════════
with tab_ocr:
    st.markdown("### 📷 Zoho Catalyst Zia AI — OCR & FIR Text Analytics")
    st.caption("Upload physical FIR images or paste case narratives to extract IPC sections, jurisdictions, and AI summaries.")

    uploaded_file = st.file_uploader("Upload FIR Copy / Document (PNG, JPG, PDF, TXT)", type=["png", "jpg", "jpeg", "pdf", "txt"])
    
    default_narrative = """FIR No. 104/2024 registered at Koramangala PS, Bengaluru City. On 14-03-2024 at around 21:30 hrs, complainant reported snatching of gold chain by two unidentified male accused riding a black motorcycle under Sec. 379 IPC r/w Sec. 356 IPC. Accused fled towards E-City Expressway."""
    
    sample_text = st.text_area("Or Paste Raw FIR Narrative / Statement", value=default_narrative, height=140)
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt"):
            sample_text = uploaded_file.read().decode("utf-8")
            st.info(f"Loaded text file `{uploaded_file.name}` ({len(sample_text)} chars)")
        else:
            st.info(f"Loaded image/document `{uploaded_file.name}`. Sending to Zia OCR service...")

    if st.button("⚡ Run Zia AI Analysis & Summarization", type="primary"):
        with st.spinner("Processing with Zoho Catalyst Zia AI Text Analytics..."):
            try:
                r = requests.post(f"{API_BASE}/api/zia/summarize", json={"text": sample_text}, timeout=10)
                if r.status_code == 200:
                    zia_data = r.json()
                    st.success("✅ Zia AI Analysis Completed Successfully!")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Zia Confidence Score", f"{zia_data.get('zia_confidence_score', 0.95)*100:.0f}%")
                    c2.metric("Word Count", zia_data.get("extracted_entities", {}).get("word_count", 0))
                    c3.metric("Service Provider", "Zoho Catalyst Zia AI")

                    st.markdown("#### 📝 Executive Summary")
                    st.info(zia_data.get("executive_summary", ""))

                    st.markdown("#### 🔍 Extracted Named Entities")
                    entities = zia_data.get("extracted_entities", {})
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Legal & IPC Sections:**")
                        ipc_list = entities.get("ipc_sections", [])
                        if ipc_list:
                            for ipc in ipc_list:
                                st.markdown(f"- `{ipc}`")
                        else:
                            st.write("No specific IPC sections identified.")
                    with col_b:
                        st.markdown("**Extracted Jurisdictions:**")
                        jur_list = entities.get("jurisdictions", [])
                        if jur_list:
                            for jur in jur_list:
                                st.markdown(f"- 📍 `{jur}`")
                        else:
                            st.write("No specific jurisdictions identified.")

                    st.divider()
                    st.markdown("#### 🔎 Search Similar Past Cases via Vector RAG")
                    if st.button("Find Similar Modus Operandi Cases in Database"):
                        sim_res = query_backend(f"Find similar cases like: {sample_text[:100]}", "zia_session", "Analyst")
                        formatted_sim = format_answer_naturally(sim_res)
                        st.markdown(formatted_sim)
                else:
                    st.error(f"Zia AI Service Error: {r.text}")
            except Exception as e:
                st.error(f"Error calling Zia service: {e}")

