# Intelligent Conversational AI & Crime Analytics Platform

An intelligent, conversational AI and crime analytics platform designed for the state crime database. It enables investigators, analysts, and policymakers to interact with the database using natural language queries, providing advanced analytical capabilities grounded in criminology and sociological insights.

## Project Architecture & Stages

### Stage 1: Data Engineering & Foundation
- Database setup based on relational ER diagram.
- ETL pipelines for historical and real-time FIR data ingestion.
- Implementation of Role-Based Access Control (RBAC).

### Stage 2: Core Conversational AI & Search
- Natural Language Understanding (NLU) engine for English and regional languages (Kannada).
- Retrieval-Augmented Generation (RAG) for querying unstructured FIR data (`BriefFacts`).
- Voice interaction support (STT/TTS).

### Stage 3: Advanced Analytics & Graph Intelligence
- Criminal network analysis utilizing Graph Databases.
- Geospatial mapping for crime hotspots based on location coordinates.
- Offender profiling and behavioral risk scoring.

### Stage 4: User Interface & Experience
- Comprehensive dashboard for analytics and chat interface.
- Case summary and conversation export to PDF.

### Stage 5: Explainable AI (XAI) & Deployment
- Explainable AI with data citations linked to `CrimeNo` or `CaseMasterID`.
- Secure on-premise or sovereign cloud deployment.

## Tech Stack

- **Frontend:** Next.js (React)
- **Backend:** Python (FastAPI)
- **AI / LLM Framework:** LlamaIndex / LangChain
- **LLM Models:** Local Open Source Models (e.g., Llama 3, Mistral) hosted via vLLM/Ollama
- **Translation / Voice:** Bhashini & OpenAI Whisper
- **Databases:**
  - **Relational:** PostgreSQL (with PostGIS for spatial data)
  - **Graph:** Neo4j (for network/relationship analysis)
  - **Vector Database:** Milvus or Qdrant (for RAG unstructured search)

## Folder Structure

- `/frontend/` - Next.js web application
- `/backend/` - FastAPI Python server
- `/docs/` - Project documentation and schemas

## Getting Started

*(Instructions for running the project will be added as the setup progresses)*
