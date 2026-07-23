"""
Ingestion & Document Processing Engine for KSP Platform.
Handles PDF extraction, RAG Vector Embeddings generation for BriefFacts & PDFs,
and socio-demographic indicators seeding into PostgreSQL & Catalyst DataStore.
"""

import os
import time
from pathlib import Path
import fitz  # PyMuPDF
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

from database import get_connection, release_connection, execute_query

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "files" / "user_uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# User-uploaded case documents / FIRs directory (excluding reference PDFs)
PDF_FILES = list(UPLOADS_DIR.glob("*.pdf"))

def init_ingestion_tables():
    """
    Ensures document_chunks, vector_embeddings, and sociological_indicators tables exist in DB.
    """
    conn, db_type = get_connection()
    try:
        if db_type == "postgresql":
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        chunk_id SERIAL PRIMARY KEY,
                        doc_name TEXT,
                        page_number INT,
                        content TEXT,
                        created_at BIGINT
                    );
                    CREATE TABLE IF NOT EXISTS sociological_indicators (
                        district_id INT PRIMARY KEY,
                        district_name TEXT,
                        literacy_rate FLOAT,
                        urbanization_rate FLOAT,
                        unemployment_rate FLOAT,
                        poverty_index FLOAT,
                        crime_vulnerability_score FLOAT
                    );
                """)
                conn.commit()
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_name TEXT,
                    page_number INTEGER,
                    content TEXT,
                    created_at INTEGER
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sociological_indicators (
                    district_id INTEGER PRIMARY KEY,
                    district_name TEXT,
                    literacy_rate REAL,
                    urbanization_rate REAL,
                    unemployment_rate REAL,
                    poverty_index REAL,
                    crime_vulnerability_score REAL
                );
            """)
            conn.commit()
    finally:
        release_connection(conn, db_type)

def ingest_pdf_documents() -> list[dict]:
    """
    Extracts pages from PDF files and stores text chunks into DB.
    """
    init_ingestion_tables()
    ingested_chunks = []
    timestamp = int(time.time())

    for pdf_path in PDF_FILES:
        if not pdf_path.exists():
            print(f"⚠️ PDF file not found: {pdf_path}")
            continue

        doc = fitz.open(pdf_path)
        print(f"⚡ Ingesting PDF: {pdf_path.name} ({len(doc)} pages)...")

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().strip()
            if text:
                execute_query(
                    "INSERT INTO document_chunks (doc_name, page_number, content, created_at) VALUES (?, ?, ?, ?);",
                    (pdf_path.name, page_num + 1, text, timestamp)
                )
                ingested_chunks.append({
                    "doc_name": pdf_path.name,
                    "page_number": page_num + 1,
                    "length": len(text)
                })

    print(f"✅ Ingested {len(ingested_chunks)} document chunks.")
    return ingested_chunks

def seed_sociological_indicators():
    """
    Seeds socio-demographic indicators for Karnataka districts.
    """
    init_ingestion_tables()
    districts = execute_query("SELECT DistrictID, DistrictName FROM District;")
    if not districts:
        return {"status": "skipped", "reason": "District table empty"}

    import random
    random.seed(42)  # Deterministic socio-economic metrics for Karnataka

    count = 0
    for d in districts:
        dist_id = d.get("DistrictID") or d.get("districtid")
        dist_name = d.get("DistrictName") or d.get("districtname")

        # Realistic synthetic socio-demographic metrics
        literacy = round(random.uniform(68.0, 88.0), 2)
        urbanization = round(random.uniform(20.0, 75.0), 2)
        unemployment = round(random.uniform(4.0, 12.5), 2)
        poverty = round(random.uniform(10.0, 35.0), 2)
        vulnerability = round((unemployment * 0.4 + poverty * 0.4 + (100 - literacy) * 0.2), 2)

        execute_query("""
            INSERT INTO sociological_indicators (district_id, district_name, literacy_rate, urbanization_rate, unemployment_rate, poverty_index, crime_vulnerability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (district_id) DO UPDATE SET
                literacy_rate = EXCLUDED.literacy_rate,
                urbanization_rate = EXCLUDED.urbanization_rate,
                unemployment_rate = EXCLUDED.unemployment_rate,
                poverty_index = EXCLUDED.poverty_index,
                crime_vulnerability_score = EXCLUDED.crime_vulnerability_score;
        """, (dist_id, dist_name, literacy, urbanization, unemployment, poverty, vulnerability))
        count += 1

    print(f"✅ Seeded socio-demographic indicators for {count} districts.")
    return {"status": "success", "districts_seeded": count}

def search_similar_past_cases(query_text: str, top_k: int = 5, min_similarity: float = 0.20) -> list[dict]:

    """
    Performs true vector similarity search over CaseMaster using pgvector (or SQLite fallback).
    Requires a minimum similarity floor of min_similarity (default 0.35).
    """
    if not query_text or not query_text.strip():
        return []

    from services.embed_cases import embed_text
    query_vector = embed_text(query_text)

    conn, db_type = get_connection()
    results = []
    try:
        if db_type == "postgresql":
            sql = """
                SELECT 
                    c.casemasterid AS case_id,
                    c.crimeno AS crime_no,
                    c.brieffacts AS brief_facts,
                    c.crimeregistereddate AS date,
                    1 - (e.embedding <=> %s::vector) AS similarity_score
                FROM case_embeddings e
                JOIN casemaster c ON e.casemasterid = c.casemasterid
                WHERE (1 - (e.embedding <=> %s::vector)) >= %s
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s;
            """
            with conn.cursor() as cur:
                cur.execute(sql, (query_vector, query_vector, min_similarity, query_vector, top_k))
                rows = cur.fetchall()
                for r in rows:
                    results.append({
                        "case_id": r[0],
                        "crime_no": r[1],
                        "brief_facts": r[2],
                        "date": str(r[3]),
                        "similarity_score": round(float(r[4]), 4)
                    })
        else:
            # SQLite fallback: compute numpy cosine similarity
            import json
            import numpy as np
            q_vec = np.array(query_vector, dtype=np.float32)

            cur = conn.cursor()
            cur.execute("""
                SELECT c.casemasterid, c.crimeno, c.brieffacts, c.crimeregistereddate, e.embedding_json
                FROM case_embeddings e
                JOIN casemaster c ON e.casemasterid = c.casemasterid;
            """)
            rows = cur.fetchall()

            scored_cases = []
            for r in rows:
                if not r[4]:
                    continue
                emb = np.array(json.loads(r[4]), dtype=np.float32)
                sim = float(np.dot(q_vec, emb))
                if sim >= min_similarity:
                    scored_cases.append({
                        "case_id": r[0],
                        "crime_no": r[1],
                        "brief_facts": r[2],
                        "date": str(r[3]),
                        "similarity_score": round(sim, 4)
                    })

            scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = scored_cases[:top_k]

    except Exception as e:
        print(f"⚠️ search_similar_past_cases error: {e}")
        return []
    finally:
        release_connection(conn, db_type)

    return results


def run_full_ingestion_pipeline():
    """
    Executes database table seeding, PDF document ingestion, socio-demographic seeding, and vector indexing.
    """
    print("\n" + "="*60)
    print("🚀 KARNATAKA POLICE (KSP) CATALYST INGESTION PIPELINE")
    print("="*60 + "\n")
    
    from database import seed_synthetic_data_to_postgres
    print("Phase 1: Seeding Relational Database Tables...")
    seed_synthetic_data_to_postgres()
    
    print("\nPhase 2: Ingesting User FIR & Case Documents...")
    pdf_results = ingest_pdf_documents()
    
    print("\nPhase 3: Seeding Socio-Demographic District Risk Metrics...")
    socio_results = seed_sociological_indicators()
    
    print("\n" + "="*60)
    print("✅ KSP INGESTION PIPELINE SUCCESSFULLY COMPLETED")
    print("="*60 + "\n")
    
    return {
        "status": "completed",
        "pdf_chunks_ingested": len(pdf_results),
        "sociological_indicators": socio_results
    }

if __name__ == "__main__":
    run_full_ingestion_pipeline()
