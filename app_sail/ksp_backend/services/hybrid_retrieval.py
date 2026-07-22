"""
PostgreSQL Hybrid Query & Tantivy BM25 Re-Ranking Engine for KSP Platform.
Combines structured SQL constraints (District, Year, Crime Type, IPC sections)
with Tantivy full-text BM25 keyword scoring on CaseMaster.BriefFacts narratives.
"""

import re
import logging
import tantivy
from database import execute_query

logger = logging.getLogger(__name__)



def _tokenize_text(text: str) -> list[str]:
    """Tokenize text into lowercased words for BM25 scoring."""
    if not text:
        return []
    return [w.lower() for w in re.findall(r'\w+', str(text)) if len(w) > 2]


def execute_hybrid_search(intent_data: dict, raw_query: str, top_k: int = 10) -> tuple[list[dict], str]:
    """
    1. Builds dynamic PostgreSQL SQL query with exact slot filters:
       - district ILIKE
       - year (crimeregistereddate LIKE)
       - crime_type (canonical CrimeHead group + narrative keywords + IPC sections)
       - keywords / IPC sections (brieffacts ILIKE)
    2. Fetches candidate pool (up to 40 candidates).
    3. Uses BM25Okapi on candidate BriefFacts narratives to score and re-rank.
    4. Strict Zero-Row Integrity: Never returns unrelated fallback cases if 0 match.
    """
    district = intent_data.get("district")
    year = intent_data.get("year")
    crime_type = intent_data.get("crime_type")
    ipc_sections = intent_data.get("ipc_sections") or []
    keywords = intent_data.get("search_keywords") or []

    # Clean keywords from query if keywords array was empty
    if not keywords and raw_query:
        stopwords = {"show", "me", "recent", "crimes", "cases", "case", "in", "the", "district", "year", "find", "all", "get", "list", "total", "summarise", "summarize", "human", "city", "bengaluru", "mysuru", "mangaluru", "belagavi", "hubballi", "dharwad", "karnataka", "state"}
        words = [w.lower() for w in re.findall(r'\w+', raw_query) if len(w) > 2 and w.lower() not in stopwords]
        keywords = words[:4]


    # Special phrase check for human trafficking
    if raw_query and "traffick" in raw_query.lower() and "traffick" not in keywords:
        keywords.append("traffick")

    sql = """
        SELECT
            c.casemasterid AS CaseMasterID,
            c.crimeno AS CrimeNo,
            c.crimeregistereddate AS CrimeRegisteredDate,
            c.brieffacts AS BriefFacts,
            d.districtname AS DistrictName,
            ch.crimegroupname AS CrimeGroupName
        FROM casemaster c
        JOIN unit u ON c.policestationid = u.unitid
        JOIN district d ON u.districtid = d.districtid
        LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
        WHERE 1=1
    """
    params = []

    accused_id = intent_data.get("accused_id")
    case_no = intent_data.get("case_no")
    is_topic = intent_data.get("is_topic_query", False)

    # 1. District filter
    if district:
        sql += " AND d.districtname ILIKE %s"
        params.append(f"%{district}%")

    # 2. Year filter
    if year:
        sql += " AND c.crimeregistereddate LIKE %s"
        params.append(f"%{year}%")

    # 3. Accused ID filter
    if accused_id:
        has_specific_filter = True
        sql += " AND c.casemasterid IN (SELECT casemasterid FROM accused WHERE accusedmasterid = %s OR personid = %s)"
        params.extend([accused_id, accused_id])

    # 4. Canonical Crime Type & Keyword Synonym Mapping
    where_or_clauses = []
    has_specific_filter = False

    if crime_type:
        has_specific_filter = True
        c_lower = crime_type.lower()
        if any(term in c_lower for term in ["murder", "homicide", "killing", "death", "302"]):
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%Body%", "%murder%", "%homicide%", "%302%"])
        elif any(term in c_lower for term in ["traffick", "human trafficking", "370", "immoral"]):
            where_or_clauses.extend(["c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%traffick%", "%370%", "%immoral%"])
        elif any(term in c_lower for term in ["assault", "molestation", "modesty", "women", "354"]):
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%Body%", "%assault%", "%modesty%"])
        elif any(term in c_lower for term in ["cyber", "fraud", "cheating", "online", "420"]):
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%Documents%", "%fraud%", "%cyber%"])
        elif any(term in c_lower for term in ["theft", "robbery", "snatching", "stolen", "379", "356"]):
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%Property%", "%theft%", "%snatching%"])
        elif any(term in c_lower for term in ["driving", "accident", "rash", "279"]):
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend(["%Misc%", "%driving%"])
        else:
            where_or_clauses.extend(["ch.crimegroupname ILIKE %s", "c.brieffacts ILIKE %s"])
            params.extend([f"%{crime_type}%", f"%{crime_type}%"])

    for kw in keywords[:3]:
        if kw.lower() in ["human", "cases", "case", "city", "bengaluru", "mysuru", "mangaluru", "belagavi", "hubballi", "dharwad", "karnataka", "state"]:
            continue
        has_specific_filter = True
        where_or_clauses.append("c.brieffacts ILIKE %s")
        params.append(f"%{kw}%")

    for ipc in ipc_sections[:2]:
        has_specific_filter = True
        where_or_clauses.append("c.brieffacts ILIKE %s")
        params.append(f"%{ipc}%")

    if where_or_clauses:
        sql += f" AND ({' OR '.join(where_or_clauses)})"

    sql += " ORDER BY c.casemasterid DESC LIMIT 40;"

    # Execute candidate search
    try:
        candidates = execute_query(sql, tuple(params) if params else ())
    except Exception as e:
        logger.debug(f"Primary SQL Search Fallback ({e})")
        sql_fallback = "SELECT casemasterid AS CaseMasterID, crimeno AS CrimeNo, crimeregistereddate AS CrimeRegisteredDate, brieffacts AS BriefFacts FROM casemaster ORDER BY casemasterid DESC LIMIT 30;"
        candidates = execute_query(sql_fallback)

    # 4. Strict Zero-Row Return: If a specific crime/keyword was queried and 0 matched, return []
    # Do NOT inject random unrelated cases (e.g. Rash Driving for Murder / Trafficking queries!)
    specific_query_terms = ["traffick", "murder", "homicide", "theft", "robbery", "cyber", "fraud", "extortion", "narcotic", "ndps", "kidnap", "abduct", "assault", "molest", "dowry", "rape", "370", "302", "379", "420"]
    is_topic_query = is_topic or has_specific_filter or any(t in raw_query.lower() for t in specific_query_terms)

    if not candidates:
        if is_topic_query:
            logger.debug(f"0 records matched strict filters for crime_type='{crime_type}', keywords={keywords}. Zero false-match return.")
            return [], sql


        # Only if user asked a generic query without specific topic ("Show all crimes in 2023"), return latest cases
        relaxed_sql = """
            SELECT c.casemasterid AS CaseMasterID, c.crimeno AS CrimeNo, c.crimeregistereddate AS CrimeRegisteredDate, c.brieffacts AS BriefFacts, d.districtname AS DistrictName
            FROM casemaster c
            JOIN unit u ON c.policestationid = u.unitid
            JOIN district d ON u.districtid = d.districtid
            WHERE 1=1
        """
        relaxed_params = []
        if district:
            relaxed_sql += " AND d.districtname ILIKE %s"
            relaxed_params.append(f"%{district}%")
        if year:
            relaxed_sql += " AND c.crimeregistereddate LIKE %s"
            relaxed_params.append(f"%{year}%")
        relaxed_sql += " ORDER BY c.casemasterid DESC LIMIT 30;"
        candidates = execute_query(relaxed_sql, tuple(relaxed_params) if relaxed_params else ())

    if not candidates:
        return [], sql


    # 5. Tantivy BM25 Re-Ranking on Candidate BriefFacts
    if candidates and raw_query:
        try:
            builder = tantivy.SchemaBuilder()
            builder.add_integer_field("doc_idx", stored=True)
            builder.add_text_field("brief_facts", stored=True)
            schema = builder.build()

            index = tantivy.Index(schema)
            writer = index.writer()

            for idx, r in enumerate(candidates):
                text = str(r.get("BriefFacts") or r.get("brieffacts") or "")
                writer.add_document(tantivy.Document(doc_idx=[idx], brief_facts=[text]))

            writer.commit()
            index.reload()
            searcher = index.searcher()

            clean_query = " ".join(re.findall(r'\w+', raw_query))
            if clean_query:
                query = index.parse_query(clean_query, ["brief_facts"])
                results = searcher.search(query, len(candidates))

                scores_map = {}
                for score, doc_address in results.hits:
                    doc = searcher.doc(doc_address)
                    doc_dict = doc.to_dict()
                    doc_idx = doc_dict["doc_idx"][0]
                    scores_map[doc_idx] = round(float(score), 4)

                for idx, r in enumerate(candidates):
                    r["_bm25_score"] = scores_map.get(idx, 0.0)

                candidates.sort(key=lambda x: x.get("_bm25_score", 0.0), reverse=True)
        except Exception as e:
            logger.debug(f"Tantivy BM25 Scoring Error: {e}")
            for r in candidates:
                r["_bm25_score"] = 0.0


    return candidates[:top_k], sql

