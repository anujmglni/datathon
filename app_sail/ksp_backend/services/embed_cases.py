"""
Batch Embedding Pipeline for KSP Platform.
Generates 384-dimensional dense vector embeddings using sentence-transformers (all-MiniLM-L6-v2)
for all ~8,000 cases in CaseMaster.BriefFacts and persists them into case_embeddings.
"""

import sys
import time
import json
import logging
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path to allow importing database module
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_connection, release_connection, execute_query

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_model_instance = None

def get_embedding_model():
    """Returns cached SentenceTransformer model instance."""
    global _model_instance
    if _model_instance is None:
        print(f"📦 Loading embedding model '{MODEL_NAME}'...")
        _model_instance = SentenceTransformer(MODEL_NAME)
        print("✅ Model loaded successfully.")
    return _model_instance

def embed_text(text: str) -> list[float]:
    """Generates a 384-dim normalized vector for a single text string."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()

def embed_all_cases(batch_size: int = 250):
    """
    Fetches all cases from CaseMaster, generates embeddings in batches,
    and inserts/upserts them into case_embeddings table.
    """
    print("\n" + "="*60)
    print("🚀 BATCH EMBEDDING PIPELINE (pgvector / SQLite)")
    print("="*60 + "\n")

    conn, db_type = get_connection()
    try:
        # Fetch all cases
        if db_type == "postgresql":
            with conn.cursor() as cur:
                cur.execute("SELECT casemasterid, brieffacts FROM casemaster ORDER BY casemasterid ASC;")
                rows = cur.fetchall()
                cases = [{"casemasterid": r[0], "brieffacts": r[1]} for r in rows]
        else:
            cur = conn.cursor()
            cur.execute("SELECT casemasterid, brieffacts FROM casemaster ORDER BY casemasterid ASC;")
            rows = cur.fetchall()
            cases = [{"casemasterid": r[0], "brieffacts": r[1]} for r in rows]

        total_cases = len(cases)
        print(f"📊 Found {total_cases} total cases in database to embed.")

        if total_cases == 0:
            print("⚠️ No cases found in database. Exiting batch embedding.")
            return

        model = get_embedding_model()
        timestamp = int(time.time())

        processed = 0
        start_time = time.time()

        for i in range(0, total_cases, batch_size):
            batch = cases[i : i + batch_size]
            texts = [b["brieffacts"] if (b.get("brieffacts") and str(b.get("brieffacts")).strip()) else "Case facts not recorded" for b in batch]
            
            # Batch vector encoding
            embeddings = model.encode(texts, batch_size=len(batch), convert_to_numpy=True, normalize_embeddings=True)

            if db_type == "postgresql":
                with conn.cursor() as cur:
                    for case_obj, emb in zip(batch, embeddings):
                        cid = case_obj["casemasterid"]
                        emb_list = emb.tolist()
                        cur.execute("""
                            INSERT INTO case_embeddings (casemasterid, source_field, embedding, created_at)
                            VALUES (%s, 'brieffacts', %s::vector, %s)
                            ON CONFLICT (casemasterid) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                created_at = EXCLUDED.created_at;
                        """, (cid, emb_list, timestamp))
                conn.commit()
            else:
                for case_obj, emb in zip(batch, embeddings):
                    cid = case_obj["casemasterid"]
                    emb_json = json.dumps(emb.tolist())
                    conn.execute("""
                        INSERT INTO case_embeddings (casemasterid, source_field, embedding_json, created_at)
                        VALUES (?, 'brieffacts', ?, ?)
                        ON CONFLICT(casemasterid) DO UPDATE SET
                            embedding_json = excluded.embedding_json,
                            created_at = excluded.created_at;
                    """, (cid, emb_json, timestamp))
                conn.commit()

            processed += len(batch)
            elapsed = round(time.time() - start_time, 2)
            rate = round(processed / (elapsed + 0.001), 1)
            print(f"   Processed {processed}/{total_cases} cases ({round(processed/total_cases*100, 1)}%) - {rate} cases/sec")

        # 3. Post-Ingestion ANALYZE Step
        print("\n⚡ Running database ANALYZE on case_embeddings table to update statistics...")
        if db_type == "postgresql":
            with conn.cursor() as cur:
                cur.execute("ANALYZE case_embeddings;")
            conn.commit()
        else:
            conn.execute("ANALYZE case_embeddings;")
            conn.commit()
        print("✅ ANALYZE case_embeddings completed successfully.")

        print(f"\n🎉 Successfully embedded and indexed {processed} cases in {round(time.time() - start_time, 2)}s!")

    finally:
        release_connection(conn, db_type)

if __name__ == "__main__":
    embed_all_cases()
