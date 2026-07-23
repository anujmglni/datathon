# Karnataka Police Conversational Crime Intelligence & Network Analysis Platform

This README provides a comprehensive, file-by-file codebase guide designed to give Claude (or any AI assistant) full context on the architecture, features, data models, NLU pipelines, and technical implementations completed in this repository.

---

## 📌 Executive Summary & Project Goal

The **KSP Crime Intelligence Platform** is an enterprise-grade AI analytics and network intelligence system built for the **Karnataka State Police (KSP)**. It enables law enforcement officers, crime analysts, and senior officials to perform natural language inquiries across historical crime records, visualize criminal networks, analyze spatial-temporal trends, enforce Role-Based Access Control (RBAC), and export official case reports.

The platform is engineered for deployment on **Zoho Catalyst (AppSail)** with a **FastAPI backend**, a **Next.js 15 (React 19 + Tailwind CSS) frontend**, and a dual **PostgreSQL / SQLite database engine**.

---

## 🏗️ System Architecture & Tech Stack

```
                              ┌────────────────────────────────────────┐
                              │    Next.js 15 Frontend (AppSail)      │
                              │  - 4 Main Tabs: Chat, Network,         │
                              │    Analytics, Report Compiler          │
                              │  - Recharts, Leaflet Map, Live Trace   │
                              └───────────────────┬────────────────────┘
                                                  │ HTTP REST APIs
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │     FastAPI Backend (AppSail:8080)     │
                              └───────┬────────────────────────┬───────┘
                                      │                        │
             ┌────────────────────────┴───────┐        ┌───────┴────────────────────────┐
             │  Zero-Shot NLU Intent Agent    │        │ Specialized Intelligence Engine│
             │  - 8 Skill Intents             │        │  - Hybrid SQL + BM25 Search    │
             │  - Slot Retention & Context    │        │  - NetworkX Graph Algorithms   │
             │  - Explainable AI (XAI)        │        │  - Analytics Pre-Aggregation   │
             │  - RBAC Governance & Audit     │        │  - ReportLab PDF / DOCX Gen    │
             └────────────────────────────────┘        └────────────────────────────────┘
                                      │                        │
                                      ▼                        ▼
                              ┌────────────────────────────────────────┐
                              │ PostgreSQL (Catalyst DataStore/Neon)   │
                              │       [Fallback: Local SQLite]         │
                              └────────────────────────────────────────┘
```

### Key Technologies:
- **Backend Framework**: Python 3.11, FastAPI, Uvicorn, Pydantic.
- **Frontend Framework**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide React.
- **Data Visualization**: Recharts (Analytics), Leaflet / React-Leaflet (Karnataka Map), Canvas / Vis-style graph layout (Network Graph).
- **Data Storage**: PostgreSQL (`psycopg2` Threaded Connection Pool), SQLite (`ksp_local.db` fallback).
- **NLU & AI**: Groq / Anthropic Claude / OpenAI Zero-Shot NLU, Vector Cosine Similarity / Tantivy BM25 Re-Ranking.
- **Graph Processing**: NetworkX (Community detection, centrality, hub identification).
- **Document Export**: ReportLab (PDF), `python-docx` (DOCX).
- **Cloud Infrastructure**: Zoho Catalyst AppSail (Container hosting), Zoho Catalyst DataStore.

---

## 🗄️ Database Schema & Data Models

The database models realistic Karnataka Police crime data across 6 primary entities:

1. `CaseMaster`: Core FIR record (CaseID, FIRNo, District, PoliceStation, CrimeMajorHead, CrimeMinorHead, DateOfOccurrence, BriefFacts, Status, etc.).
2. `FIRDetails`: Extended FIR details including IPC/BNS sections, Investigating Officer ID, and modus operandi.
3. `AccusedDetails`: Offender profiles (AccusedID, CaseID, Name, Age, Gender, Address, RecidivismScore, PriorConvictions, Status).
4. `VictimDetails`: Victim records (VictimID, CaseID, Name, Age, Gender, InjuryType, LossAmount).
5. `FinancialTransactions`: Cybercrime money trails (TxnID, CaseID, SenderAcc, RecipientAcc, Amount, BankName, FraudCategory, Status).
6. `AuditLog`: Immutable governance trail (LogID, UserID, UserRole, QueryString, SQLExecuted, RowsTouched, Timestamp).

---

## 📁 Detailed File-by-File Breakdown

Below is the complete file-by-file directory explaining the exact function and responsibility of every file in the project.

### 🌐 Root Directory & Data Utilities

- **[`generate_synthetic_data.py`](file:///Users/muditagrawal/Projects/KSP/generate_synthetic_data.py)**
  - Synthetic dataset generator creating thousands of realistic FIR records across all 38 Karnataka police districts.
  - Generates connected criminal networks, shared bank accounts, victim profiles, IPC section mappings, and spatial coordinates for map visualizations.

- **[`datastore-schema.json`](file:///Users/muditagrawal/Projects/KSP/datathon/datastore-schema.json)**
  - Declarative schema definition for Zoho Catalyst DataStore, specifying table structures, column data types, foreign keys, and indexes.

- **[`catalyst.json`](file:///Users/muditagrawal/Projects/KSP/datathon/catalyst.json)** & **[`.catalystrc`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/.catalystrc)**
  - Project setup configurations for the Zoho Catalyst CLI, registering the AppSail container deployment target and build scripts.

---

### ⚙️ Backend Services (`app_sail/ksp_backend/`)

#### 1. Core API & Database Engine
- **[`app.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/app.py)**
  - Main FastAPI application server.
  - Endpoints exposed:
    - `POST /api/query`: Primary NLU conversational query processor (intents, hybrid search, RAG synthesis, RBAC, audit logging).
    - `GET /api/network`: 3-Column Criminal Network Graph endpoint (returns nodes, edges, filter state, 300-node cap status).
    - `GET /api/network/options`: Dropdown filter choices for network graph (districts, crime heads).
    - `GET /api/network/profile`: Offender/Entity dossier lookups.
    - `GET /api/analytics/summary`: Aggregate analytics data for all 8 charts and Karnataka map coordinates.
    - `POST /api/report/generate`, `POST /api/report/export_docx`: Instant PDF/DOCX report compilers.
    - `POST /api/graph/rebuild`, `POST /api/graph/summary`: NetworkX graph processing & LLM summary synthesis.
    - `POST /api/zia/summarize`: Zoho Catalyst Zia AI text analytics & entity extractor for raw FIR text.
    - `POST /api/ingest/run`: Data ingestion trigger.

- **[`database.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/database.py)**
  - Threaded PostgreSQL connection pool manager (`psycopg2.pool.ThreadedConnectionPool`).
  - Seamless fallback to local SQLite (`ksp_local.db`) if a live PostgreSQL daemon is not detected, enabling zero-config local development.
  - Automatic `AuditLog` table initialization.

#### 2. Agent NLU & Governance (`agent/`)
- **[`agent/intent_classifier.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/agent/intent_classifier.py)**
  - Zero-Shot LLM Natural Language Understanding (NLU) engine.
  - Classifies incoming natural language queries into 8 specialized skills:
    1. `SQL_ANALYTICS`: Statistical totals, counts, IPC section volumes.
    2. `NETWORK_ANALYSIS`: Gang networks, co-accused links, accomplices.
    3. `RAG_NARRATIVE`: Narrative text search over FIR BriefFacts and MO.
    4. `OFFENDER_PROFILE`: Recidivism risk, habitual offender histories.
    5. `FINANCIAL_LINK`: Cybercrime money trails, bank account links.
    6. `FORECASTING`: Hotspot projections, time-series trends.
    7. `SOCIOLOGICAL`: Socio-demographic correlations (literacy, poverty).
    8. `DOC_GEN`: PDF/DOCX report exports.
  - Extracts active slots (`district`, `year`, `crime_type`, `ipc_sections`, `accused_id`, `case_no`, `search_keywords`) and rewrites follow-up turns into contextual `standalone_query` strings.

- **[`agent/llm_synthesizer.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/agent/llm_synthesizer.py)**
  - Translates raw SQL query result rows and vector search hits into clear, professional investigative intelligence briefs written for police officers.
  - Formats output with key findings, executive summaries, evidence tables, and actionable next steps.

- **[`agent/governance.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/agent/governance.py)**
  - Role-Based Access Control (RBAC) & Governance module.
  - Enforces field redaction (masking PII, sensitive details) based on officer roles (`Officer`, `Analyst`, `Admin`).
  - Inserts all query metadata, compiled SQL, and execution metrics into an immutable audit trail.

- **[`agent/session.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/agent/session.py)**
  - Multi-turn conversation state manager.
  - Retains history context across turns and preserves active search slots (e.g. remembering that the user is currently inquiring about "Bengaluru City" in "2024").

#### 3. Domain Services (`services/`)
- **[`services/hybrid_retrieval.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/hybrid_retrieval.py)**
  - Hybrid search engine combining dynamic PostgreSQL slot filtering (district, year, crime head) with Tantivy BM25 keyword re-ranking over narrative text.

- **[`services/network_service.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/network_service.py)**
  - Dedicated service for the 3-Column Interactive Criminal Network Graph.
  - Connects Accused, Victim, Location, and Financial nodes.
  - Enforces a **300-node cap** for smooth frontend rendering.
  - Fetches deep offender dossier profiles for selected nodes.

- **[`services/analytics_service.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/analytics_service.py)**
  - Pre-aggregates analytics data for 8 charts (district distribution, monthly crime trends, crime major heads, age/gender breakdowns, financial losses) and formats lat/lng markers for the Karnataka Leaflet map.

- **[`services/graph_analysis.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/graph_analysis.py)**
  - NetworkX graph engine for community detection, central suspect identification, degree centrality calculation, and total fraud volume computation.

- **[`services/pdf_report.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/pdf_report.py)**
  - Automated report builder using ReportLab (PDF) and python-docx (DOCX) with official KSP branding, headers, tables, and executive summaries.

- **[`services/ingest.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/ingest.py)**
  - Vector & text ingestion pipeline that processes raw FIR records and indexes them into vector cosine similarity and BM25 stores.

- **[`services/sync_to_catalyst.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/sync_to_catalyst.py)**
  - Exporter utility converting SQLite/Postgres tables into Catalyst DataStore JSON format.

- **[`services/verify_ingestion.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/services/verify_ingestion.py)**
  - Health check script confirming database table row counts, schema integrity, and search readiness.

#### 4. Streamlit Dashboard
- **[`streamlit_app.py`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_backend/streamlit_app.py)**
  - Full-featured standalone Streamlit dashboard serving as an alternative UI for rapid backend testing of NLU intents, network graphs, analytics, and PDF generation.

---

### 🎨 Frontend Application (`app_sail/ksp_frontend/`)

#### 1. Pages & Layout
- **[`src/app/page.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/app/page.tsx)**
  - Main application container. Manages active tab state (`chat`, `network`, `analytics`, `report`), search history, global filters, and role context.

- **[`src/app/layout.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/app/layout.tsx)**
  - Next.js root layout initializing Google Fonts (Inter), HTML head metadata, and global page layout wrappers.

- **[`src/app/globals.css`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/app/globals.css)**
  - Custom CSS stylesheet defining dark glassmorphic themes, glowing borders, custom scrollbars, animations, and Leaflet map overrides.

#### 2. Main Dashboard Components (`src/components/`)
- **[`Header.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/Header.tsx)**
  - Top navigation bar featuring the KSP crest logo, tab switches, active role selector (`Officer`, `Analyst`, `Admin`), and system health indicator.

- **[`Sidebar.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/Sidebar.tsx)**
  - Left navigation sidebar providing system telemetry, active slot summaries, preset quick queries, and session management controls.

- **[`AnalyticsTab.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/AnalyticsTab.tsx)**
  - Comprehensive 8-chart crime analytics dashboard built with Recharts.
  - Visualizations include:
    1. District Crime Breakdown
    2. Crime Major Head Distribution
    3. Monthly Crime Volume Trends
    4. Offender Age & Gender Distribution
    5. Financial Loss by Fraud Category
    6. Case Resolution & Status Rate
    7. Recidivism Risk Level Distribution
    8. Crime Occurrence Time of Day
  - Integrates the Karnataka Leaflet crime map and an AI-generated plain-language analytics summary card.

- **[`KarnatakaLeafletMap.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/KarnatakaLeafletMap.tsx)**
  - Interactive Leaflet map visualizing crime density across all 38 Karnataka districts with custom markers, popups, and district-level statistics.

- **[`NetworkGraphTab.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/NetworkGraphTab.tsx)**
  - 3-Column Interactive Criminal Network Graph.
  - Column 1: Multi-select Filter Drawer (Districts, Crime Types, Date Ranges, Link Strength, Node Types).
  - Column 2: Interactive Graph Viewport rendering Accused (Red), Victim (Green), Location (Blue), and Financial (Amber) nodes with connecting relationship edges and node cap indicators (300 nodes max).
  - Column 3: Entity Dossier Inspector displaying full criminal history, case details, prior convictions, and associated financial accounts.

- **[`ReportCompilerTab.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/ReportCompilerTab.tsx)**
  - Official Report Compiler tab allowing officers to combine chat turns, network graphs, and analytics into structured Markdown reports, previewing them in real-time and exporting to PDF or DOCX.

- **[`GroundingSources.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/GroundingSources.tsx)**
  - Explainable AI (XAI) drawer giving officers full transparency into exact compiled SQL queries, rows touched, vector similarity scores, and governance redaction status.

- **[`LiveTrace.tsx`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/components/LiveTrace.tsx)**
  - Real-time step execution stream detailing NLU intent classification, slot extraction, governance evaluation, and synthesis progress.

#### 3. API & Type Definitions (`src/lib/`)
- **[`api.ts`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/lib/api.ts)**
  - Strongly-typed API client wrapper handling fetch calls to the FastAPI backend (`processQuery`, `fetchNetworkGraph`, `fetchAnalyticsSummary`, `generatePdfReport`, `generateDocxReport`, `summarizeZiaText`).

- **[`types.ts`](file:///Users/muditagrawal/Projects/KSP/datathon/app_sail/ksp_frontend/src/lib/types.ts)**
  - TypeScript interface definitions for `QueryResponse`, `ExplainableAI`, `NetworkGraphData`, `Node`, `Edge`, `DossierProfile`, `AnalyticsSummary`, `GroundingSource`.

---

## ⚡ How to Run the Project Locally

### 1. Run the FastAPI Backend
```bash
cd app_sail/ksp_backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```
*Backend will be running at `http://localhost:8080` (API Docs at `http://localhost:8080/docs`).*

### 2. Run the Next.js Frontend
```bash
cd app_sail/ksp_frontend
npm install
npm run dev
```
*Frontend will be running at `http://localhost:3000`.*

### 3. (Optional) Run the Streamlit Testing UI
```bash
cd app_sail/ksp_backend
streamlit run streamlit_app.py
```
*Streamlit UI will be running at `http://localhost:8501`.*

---

## ✅ Completed Milestones & What Has Been Done

1. **Zero-Shot NLU Conversational Agent**: Built NLU classifier recognizing 8 intent skills with multi-turn slot retention and contextual query rewriting.
2. **Hybrid Search Architecture**: Combined dynamic PostgreSQL slot filtering with BM25 keyword re-ranking.
3. **Interactive Criminal Network Graph**: Built 3-column network visualizer with 300-node performance capping and offender dossier side-inspector.
4. **8-Chart Analytics & Karnataka Leaflet Map**: Implemented full spatial-temporal crime analytics dashboard.
5. **Governance & Audit Trail**: Integrated RBAC field redaction and immutable query logging.
6. **Automated PDF/DOCX Report Compiler**: Built instant export engines with official police formatting.
7. **Dual Database Engine**: PostgreSQL support with seamless local SQLite fallback (`ksp_local.db`).
8. **AppSail Readiness**: Fully configured container deployment settings for Zoho Catalyst AppSail.
