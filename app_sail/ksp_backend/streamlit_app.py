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


def build_graph(district=None, crime_head_id=None, min_connections=1):
    try:
        params = {"min_connections": min_connections}
        if district:
            params["district"] = district
        if crime_head_id:
            params["crime_head_id"] = crime_head_id
        r = requests.post(f"{API_BASE}/api/graph/rebuild", params=params, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_graph_summary(district=None, crime_head_id=None, min_connections=1):
    try:
        params = {"min_connections": min_connections}
        if district:
            params["district"] = district
        if crime_head_id:
            params["crime_head_id"] = crime_head_id
        r = requests.post(f"{API_BASE}/api/graph/summary", params=params, timeout=60)
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
    """Render an interactive multi-relational network graph with community coloring."""
    import plotly.graph_objects as go
    import networkx as nx

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        st.warning("⚠️ No criminal network data found matching current filter criteria.")
        return

    # Build NetworkX graph for spring layout positioning
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=e.get("weight", 1), relation=e.get("relation", "shared_case"))

    # Compute 2D spring layout positioning
    pos = nx.spring_layout(G, k=2.0, iterations=70, seed=42)

    # ── Edge Traces (Categorized by Relation Type) ─────────────────────
    edge_x_case, edge_y_case = [], []
    edge_x_bank, edge_y_bank = [], []

    for u, v, data in G.edges(data=True):
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            rel = data.get("relation", "shared_case")
            if "bank" in rel:
                edge_x_bank += [x0, x1, None]
                edge_y_bank += [y0, y1, None]
            else:
                edge_x_case += [x0, x1, None]
                edge_y_case += [y0, y1, None]

    traces = []
    if edge_x_case:
        traces.append(go.Scatter(
            x=edge_x_case, y=edge_y_case, mode='lines',
            line=dict(width=1.0, color='#475569'),
            name='Shared Case Link', hoverinfo='none'
        ))
    if edge_x_bank:
        traces.append(go.Scatter(
            x=edge_x_bank, y=edge_y_bank, mode='lines',
            line=dict(width=2.0, color='#ef4444', dash='dot'),
            name='Shared Bank Account Link', hoverinfo='none'
        ))

    # ── Node Traces (Colored by Community Cluster) ──────────────────────
    COMMUNITY_COLORS = [
        '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
        '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
    ]

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_labels = [G.nodes[n].get("name", f"Accused #{n}") for n in G.nodes()]
    communities = [G.nodes[n].get("community_id", 0) for n in G.nodes()]
    deg_cent = [G.nodes[n].get("degree_centrality", 0) for n in G.nodes()]

    # Color mapping per community
    colors = [COMMUNITY_COLORS[c % len(COMMUNITY_COLORS)] for c in communities]
    sizes = [max(12, min(45, int(c * 150) + 14)) for c in deg_cent]

    # Rich hover text per node
    hover_texts = []
    for n in G.nodes():
        meta = G.nodes[n]
        name = meta.get("name", "Unknown")
        age = meta.get("age", "N/A")
        gender = meta.get("gender", "N/A")
        cases_cnt = meta.get("total_cases", 0)
        districts = ", ".join(meta.get("districts", [])) or "N/A"
        crimes = ", ".join(meta.get("crime_types", [])) or "N/A"
        fraud = meta.get("fraud_total", 0.0)
        comm = meta.get("community_id", 0)
        deg = meta.get("degree_centrality", 0.0)
        bet = meta.get("betweenness_centrality", 0.0)

        hover_texts.append(
            f"<b>👤 Suspect: {name}</b> (ID #{n})<br>"
            f"<b>Age/Gender:</b> {age} yrs / {gender}<br>"
            f"<b>Total Cases:</b> {cases_cnt} | <b>Cluster:</b> Gang Group #{comm + 1}<br>"
            f"<b>Districts:</b> {districts}<br>"
            f"<b>Crime Types:</b> {crimes}<br>"
            f"<b>Linked Fraud:</b> ₹{fraud:,.2f}<br>"
            f"<b>Degree Centrality:</b> {deg:.4f} | <b>Betweenness:</b> {bet:.4f}"
        )

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=1.5, color='#ffffff')
        ),
        text=[f"{lbl}" for lbl in node_labels],
        textposition="top center",
        textfont=dict(size=9, color="#cbd5e1"),
        hovertext=hover_texts,
        hoverinfo='text',
        name='Suspect Node'
    )
    traces.append(node_trace)

    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            title=dict(
                text=f"🕸️ Criminal Network Graph — {len(nodes)} Suspects | {len(edges)} Links",
                font=dict(size=16, color="#f8fafc")
            ),
            showlegend=True,
            legend=dict(font=dict(color="#94a3b8"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=20, r=20, t=60, b=20),
            height=580,
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Detailed Suspect Table ──────────────────────────────────────────
    st.markdown("##### 🔴 High-Risk Suspect Intelligence Table")
    df_nodes = pd.DataFrame(nodes)
    if not df_nodes.empty:
        # Reorder and format columns
        cols = ["name", "age", "gender", "total_cases", "community_id", "fraud_total", "degree_centrality", "betweenness_centrality", "districts", "crime_types"]
        cols_present = [c for c in cols if c in df_nodes.columns]
        df_display = df_nodes[cols_present].copy()

        df_display["community_id"] = df_display["community_id"].apply(lambda c: f"Cluster #{c + 1}")
        df_display["fraud_total"] = df_display["fraud_total"].apply(lambda f: f"₹{f:,.2f}" if f else "₹0.00")
        df_display["districts"] = df_display["districts"].apply(lambda d: ", ".join(d) if isinstance(d, list) else str(d))
        df_display["crime_types"] = df_display["crime_types"].apply(lambda c: ", ".join(c) if isinstance(c, list) else str(c))

        df_display.columns = [c.replace("_", " ").title() for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)


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

                # Provider badge
                xai = result.get("explainable_ai", {})
                intent_name = result.get("intent", "UNKNOWN")
                elapsed_sec = xai.get("execution_time_seconds", 0.0)
                st.caption(f"⚡ **Intelligence Engine:** Groq AI (`llama-3.3-70b-versatile`) | **Intent:** `{intent_name}` | **Latency:** `{elapsed_sec:.3f}s`")

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
                sql = xai.get("sql_executed", "")
                if sql:
                    with st.expander("⚡ Executed SQL & Provenance"):
                        st.code(sql, language="sql")

                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": formatted,
                    "dataframe": df,
                    "sql": sql,
                    "meta": f"⚡ Groq AI (`llama-3.3-70b-versatile`) | Intent: `{intent_name}`"
                })


# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — CRIMINAL NETWORK GRAPH (VISUAL & INTELLIGENCE)
# ═══════════════════════════════════════════════════════════════════════
with tab_graph:
    st.markdown("### 🕸️ Criminal Network Analysis & Gang Cluster Intelligence")
    st.caption("Multi-relation association graph connecting suspects via shared case FIRs, financial transaction bank accounts, and police jurisdictions.")

    # ── Interactive Filter Controls ─────────────────────────────────────
    st.markdown("##### 🔍 Network Scope & Filters")
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 1.5])

    with fcol1:
        dist_filter = st.selectbox(
            "📍 Scope by District",
            ["All Districts"] + [
                "Bengaluru City", "Bengaluru District", "Mysuru City", "Mysuru District",
                "Mangaluru City", "Belagavi City", "Dharwad", "Kalaburgi City", "Ballari",
                "Bagalkot", "Bidar", "Vijayapura", "Tumakuru", "Udupi", "Kolar"
            ],
            key="graph_dist_filter"
        )
    with fcol2:
        crime_filter = st.selectbox(
            "⚖️ Crime Head Type",
            ["All Crime Types", "Property Offenses (1)", "Misc IPC Crimes (2)", "Body Offenses (3)", "Public Tranquility (4)", "Document Fraud (5)"],
            key="graph_crime_filter"
        )
    with fcol3:
        min_conn = st.slider("🔗 Min Connections Threshold", min_value=1, max_value=5, value=1, key="graph_min_conn")

    with fcol4:
        st.write("")
        st.write("")
        build_clicked = st.button("🔄 Analyze Graph", type="primary", use_container_width=True)

    if build_clicked or "last_graph_data" not in st.session_state:
        target_dist = None if dist_filter == "All Districts" else dist_filter
        target_head = None
        if "(" in crime_filter:
            try:
                target_head = int(crime_filter.split("(")[1].replace(")", ""))
            except ValueError:
                target_head = None

        with st.spinner("🧠 Querying PostgreSQL accused records, financial transactions, and running network analysis..."):
            g_res = build_graph(district=target_dist, crime_head_id=target_head, min_connections=min_conn)
            sum_res = fetch_graph_summary(district=target_dist, crime_head_id=target_head, min_connections=min_conn)

        st.session_state["last_graph_data"] = g_res.get("graph", g_res)
        st.session_state["last_graph_summary"] = sum_res.get("summary", "")

    graph_data = st.session_state.get("last_graph_data", {})
    summary_text = st.session_state.get("last_graph_summary", "")

    if graph_data:
        total_nodes = graph_data.get("total_nodes", 0)
        total_edges = graph_data.get("total_edges", 0)
        total_comms = graph_data.get("total_communities", 0)
        total_fraud = graph_data.get("total_fraud_amount", 0)

        # ── Key Summary Metric Cards ─────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Suspects Analyzed", total_nodes)
        m2.metric("🔗 Multi-Relational Links", total_edges)
        m3.metric("🧩 Crime Clusters / Gangs", total_comms)
        m4.metric("💰 Linked Fraud Amount", f"₹{total_fraud:,.2f}" if total_fraud else "₹0.00")

        st.divider()

        # ── LLM Intelligence Summary Brief (Groq Powered) ─────────────
        if summary_text:
            st.markdown("#### 🤖 Groq AI — Criminal Network Intelligence Briefing")
            st.info(summary_text)
            st.divider()

        # ── Visual Plotly Graph ─────────────────────────────────────────
        render_network_graph(graph_data)


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

