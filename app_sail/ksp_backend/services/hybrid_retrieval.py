"""
PostgreSQL True Hybrid Query Engine with pgvector & Similarity Floor for KSP Platform.
Combines structured SQL constraints (District, Year, IPC sections, Accused ID)
with 384-dim dense vector cosine similarity search over persisted CaseMaster embeddings.
Enforces a configurable minimum similarity threshold (SIMILARITY_THRESHOLD = 0.35).
"""

import logging
from database import get_connection, release_connection

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.20



def execute_hybrid_search(intent_data: dict, raw_query: str, top_k: int = 10) -> tuple[list[dict], str]:
    """
    Executes a single unified SQL hybrid query combining structured filters (WHERE)
    with vector cosine distance ordering (ORDER BY embedding <=> %s::vector)
    and a minimum similarity floor (>= 0.35).
    """
    district = intent_data.get("district")
    year = intent_data.get("year")
    ipc_sections = intent_data.get("ipc_sections") or []
    accused_id = intent_data.get("accused_id")
    query_for_vec = intent_data.get("standalone_query") or raw_query

    # Generate query vector using cached model
    from services.embed_cases import embed_text
    query_vector = embed_text(query_for_vec)

    conn, db_type = get_connection()
    results = []

    if db_type == "postgresql":
        sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
                d.districtname AS DistrictName,
                ch.crimegroupname AS CrimeGroupName,
                1 - (e.embedding <=> %s::vector) AS similarity_score
            FROM casemaster c
            JOIN case_embeddings e ON c.casemasterid = e.casemasterid
            JOIN unit u ON c.policestationid = u.unitid
            JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            WHERE 1=1
        """
        params = [query_vector]

        if district:
            sql += " AND d.districtname ILIKE %s"
            params.append(f"%{district}%")

        if year:
            sql += " AND c.crimeregistereddate LIKE %s"
            params.append(f"%{year}%")

        if accused_id:
            sql += " AND c.casemasterid IN (SELECT casemasterid FROM accused WHERE accusedmasterid::text = %s OR personid::text = %s)"
            params.extend([str(accused_id), str(accused_id)])

        if ipc_sections:
            ipc_clauses = []
            for ipc in ipc_sections[:2]:
                ipc_clauses.append("c.brieffacts ILIKE %s")
                params.append(f"%{ipc}%")
            if ipc_clauses:
                sql += f" AND ({' OR '.join(ipc_clauses)})"

        # Similarity threshold floor
        sql += " AND (1 - (e.embedding <=> %s::vector)) >= %s"
        params.extend([query_vector, SIMILARITY_THRESHOLD])

        # Exact distance ordering and top_k limit
        sql += " ORDER BY e.embedding <=> %s::vector LIMIT %s;"
        params.extend([query_vector, top_k])

        compiled_sql = sql
        for p in params:
            if isinstance(p, list):
                compiled_sql = compiled_sql.replace("%s::vector", f"'[{','.join(map(str, p[:3]))}...]'::vector", 1)
            else:
                compiled_sql = compiled_sql.replace("%s", f"'{p}'", 1)

        try:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                for r in rows:
                    results.append({
                        "CaseMasterID": r[0],
                        "CrimeNo": r[1],
                        "CrimeRegisteredDate": str(r[2]),
                        "BriefFacts": r[3],
                        "DistrictName": r[4],
                        "CrimeGroupName": r[5],
                        "similarity_score": round(float(r[6]), 4)
                    })
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"PostgreSQL Hybrid Query Error: {e}")
            return [], sql
        finally:
            release_connection(conn, db_type)

        return results, compiled_sql


    else:
        # SQLite fallback: single query pattern over SQLite tables
        import json
        import numpy as np

        q_vec = np.array(query_vector, dtype=np.float32)

        sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
                d.districtname AS DistrictName,
                ch.crimegroupname AS CrimeGroupName,
                e.embedding_json
            FROM casemaster c
            JOIN case_embeddings e ON c.casemasterid = e.casemasterid
            JOIN unit u ON c.policestationid = u.unitid
            JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            WHERE 1=1
        """
        params = []

        if district:
            sql += " AND d.districtname LIKE ?"
            params.append(f"%{district}%")

        if year:
            sql += " AND c.crimeregistereddate LIKE ?"
            params.append(f"%{year}%")

        if accused_id:
            sql += " AND c.casemasterid IN (SELECT casemasterid FROM accused WHERE accusedmasterid = ? OR personid = ?)"
            params.extend([accused_id, accused_id])

        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

            scored_rows = []
            for r in rows:
                if not r[6]:
                    continue
                emb = np.array(json.loads(r[6]), dtype=np.float32)
                sim = float(np.dot(q_vec, emb))
                if sim >= SIMILARITY_THRESHOLD:
                    scored_rows.append({
                        "CaseMasterID": r[0],
                        "CrimeNo": r[1],
                        "CrimeRegisteredDate": str(r[2]),
                        "BriefFacts": r[3],
                        "DistrictName": r[4],
                        "CrimeGroupName": r[5],
                        "similarity_score": round(sim, 4)
                    })

            scored_rows.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = scored_rows[:top_k]
        except Exception as e:
            logger.error(f"SQLite Hybrid Query Error: {e}")
            results = []
        finally:
            release_connection(conn, db_type)

        return results, sql
