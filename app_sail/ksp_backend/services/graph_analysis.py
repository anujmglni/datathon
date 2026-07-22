"""
Criminal Network Analysis Service for KSP Platform.
Uses NetworkX to build multi-relation offender association graphs:
  - Co-accused in shared cases
  - Shared bank accounts (FinancialTransaction)
  - Shared police station jurisdiction

Computes degree/betweenness centrality and community detection for
organized crime cluster identification. All SQL targets PostgreSQL.
"""

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from database import execute_query


def _fetch_accused_with_context(district_name: str = None, crime_head_id: int = None) -> list[dict]:
    """
    Fetches accused records joined with case, district, police station, IO, and crime head metadata.
    Returns rich rows with accused identity + case context.
    All SQL is PostgreSQL syntax.
    """
    sql = """
        SELECT
            a.accusedmasterid AS AccusedMasterID,
            a.casemasterid AS CaseMasterID,
            a.accusedname AS AccusedName,
            a.ageyear AS AgeYear,
            a.genderid AS GenderID,
            a.personid AS PersonID,
            c.crimeno AS CrimeNo,
            c.crimeregistereddate AS CrimeRegisteredDate,
            c.policestationid AS PoliceStationID,
            c.gravityoffenceid AS GravityOffenceID,
            c.crimemajorheadid AS CrimeMajorHeadID,
            c.policepersonid AS PolicePersonID,
            d.districtname AS DistrictName,
            u.unitname AS StationName,
            ch.crimegroupname AS CrimeGroupName,
            e.firstname AS IOName
        FROM accused a
        JOIN casemaster c ON a.casemasterid = c.casemasterid
        LEFT JOIN unit u ON c.policestationid = u.unitid
        LEFT JOIN district d ON u.districtid = d.districtid
        LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
        LEFT JOIN employee e ON c.policepersonid = e.employeeid
        WHERE 1=1

    """
    params = []

    if district_name:
        sql += " AND d.districtname ILIKE %s"
        params.append(f"%{district_name}%")

    if crime_head_id:
        sql += " AND c.crimemajorheadid = %s"
        params.append(crime_head_id)

    sql += " ORDER BY a.accusedmasterid"

    return execute_query(sql, tuple(params) if params else ())



def _fetch_financial_links() -> list[dict]:
    """
    Fetches financial transaction records to build shared-bank-account edges.
    """
    sql = """
        SELECT
            transactionid AS TransactionID,
            casemasterid AS CaseMasterID,
            accusedmasterid AS AccusedMasterID,
            fraudtype AS FraudType,
            amountlostinr AS AmountLostINR,
            amountrecoveredinr AS AmountRecoveredINR,
            bankaccountlast4 AS BankAccountLast4,
            status AS Status
        FROM financialtransaction
    """
    return execute_query(sql)


def build_criminal_network(
    district_name: str = None,
    crime_head_id: int = None,
    min_connections: int = 1,
    max_nodes: int = 150
) -> dict:
    """
    Builds a multi-relation criminal network graph with:
    - Co-accused edges (shared cases)
    - Financial edges (shared bank accounts)
    - Station edges (same police station jurisdiction)

    Returns nodes with rich metadata, edges with relation types,
    community assignments, and centrality scores.
    """
    G = nx.Graph()

    # ── 1. Fetch accused with case context ──────────────────────────────
    accused_rows = _fetch_accused_with_context(district_name, crime_head_id)

    # Build lookup maps
    accused_info = {}       # AccusedMasterID -> metadata
    case_accused_map = {}   # CaseMasterID -> [accused rows]
    station_accused_map = {}  # PoliceStationID -> [AccusedMasterIDs]

    for r in accused_rows:
        aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
        cid = r.get("CaseMasterID") or r.get("casemasterid")
        crime_no = r.get("CrimeNo") or r.get("crimeno") or f"Case #{cid}"
        name = r.get("AccusedName") or r.get("accusedname") or f"Accused #{aid}"
        age = r.get("AgeYear") or r.get("ageyear")
        gender = r.get("GenderID") or r.get("genderid")
        station = r.get("StationName") or r.get("stationname") or r.get("PoliceStationID") or r.get("policestationid")
        district = r.get("DistrictName") or r.get("districtname") or "Unknown"
        crime_group = r.get("CrimeGroupName") or r.get("crimegroupname") or "IPC Offence"
        gravity = r.get("GravityOffenceID") or r.get("gravityoffenceid")
        io_name = r.get("IOName") or r.get("ioname") or f"IO Officer (ID: {r.get('PolicePersonID') or r.get('policepersonid') or 'N/A'})"


        # Accumulate metadata per accused
        if aid not in accused_info:
            accused_info[aid] = {
                "name": name,
                "age": age,
                "gender": "Male" if gender == 1 else ("Female" if gender == 2 else "Other"),
                "cases": set(),
                "crime_numbers": set(),
                "districts": set(),
                "crime_types": set(),
                "stations": set(),
                "investigating_officers": set(),
                "heinous_count": 0,
                "fraud_total": 0.0,
            }

        info = accused_info[aid]
        info["cases"].add(cid)
        if crime_no:
            info["crime_numbers"].add(str(crime_no))
        info["districts"].add(district)
        info["crime_types"].add(crime_group)
        if station:
            info["stations"].add(str(station))
        if io_name:
            info["investigating_officers"].add(str(io_name))
        if gravity == 1:
            info["heinous_count"] += 1


        # Build case -> accused map for co-accused edges
        case_accused_map.setdefault(cid, []).append(aid)

        # Build station -> accused map for station edges
        if station:
            station_accused_map.setdefault(station, set()).add(aid)

        # Add node to graph
        G.add_node(aid)

    # ── 2. Co-accused edges (shared cases) ──────────────────────────────
    for case_id, members in case_accused_map.items():
        unique_members = list(set(members))
        if len(unique_members) > 1:
            for i in range(len(unique_members)):
                for j in range(i + 1, len(unique_members)):
                    u, v = unique_members[i], unique_members[j]
                    if G.has_edge(u, v):
                        G[u][v]["weight"] += 1.0
                        G[u][v]["shared_cases"] += 1
                    else:
                        G.add_edge(u, v, weight=1.0, relation="shared_case",
                                   shared_cases=1, shared_bank=0)

    # ── 3. Financial edges (shared bank accounts) ───────────────────────
    fin_rows = _fetch_financial_links()
    bank_accused_map = {}  # BankAccountLast4 -> [AccusedMasterIDs]

    for r in fin_rows:
        aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
        bank = r.get("BankAccountLast4") or r.get("bankaccountlast4")
        amount = r.get("AmountLostINR") or r.get("amountlostinr") or 0

        if aid in accused_info:
            accused_info[aid]["fraud_total"] += float(amount or 0)

        if bank:
            bank_accused_map.setdefault(bank, set()).add(aid)

    for bank_acct, members in bank_accused_map.items():
        members_list = [m for m in members if m in accused_info]
        if len(members_list) > 1:
            for i in range(len(members_list)):
                for j in range(i + 1, len(members_list)):
                    u, v = members_list[i], members_list[j]
                    if G.has_edge(u, v):
                        G[u][v]["weight"] += 2.0  # Financial links are higher weight
                        G[u][v]["shared_bank"] += 1
                        if G[u][v]["relation"] == "shared_case":
                            G[u][v]["relation"] = "shared_case+bank"
                    else:
                        G.add_edge(u, v, weight=2.0, relation="shared_bank",
                                   shared_cases=0, shared_bank=1)

    # ── 4. Filter by minimum connections ────────────────────────────────
    if min_connections > 1:
        low_degree = [n for n in G.nodes() if G.degree(n) < min_connections]
        G.remove_nodes_from(low_degree)

    if len(G) == 0:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "total_communities": 0,
            "total_fraud_amount": 0,
            "nodes": [],
            "edges": [],
            "communities": [],
            "top_suspects": [],
        }

    # ── 5. Centrality metrics ───────────────────────────────────────────
    degree_cent = nx.degree_centrality(G)
    betweenness_cent = nx.betweenness_centrality(G, k=min(len(G), 100))

    # ── 6. Community detection ──────────────────────────────────────────
    try:
        communities_gen = greedy_modularity_communities(G)
        communities_list = [sorted(list(c)) for c in communities_gen]
    except Exception:
        communities_list = [list(G.nodes())]

    # Assign community ID to each node
    node_community = {}
    for idx, community in enumerate(communities_list):
        for node in community:
            node_community[node] = idx

    # ── 7. Build output ─────────────────────────────────────────────────
    # Sort nodes by degree centrality, take top N
    sorted_nodes = sorted(G.nodes(), key=lambda n: degree_cent.get(n, 0), reverse=True)
    top_node_ids = set(sorted_nodes[:max_nodes])

    # Also include edges connecting top nodes
    nodes_output = []
    for nid in sorted_nodes[:max_nodes]:
        info = accused_info.get(nid, {})
        crime_types_list = list(info.get("crime_types", set()))
        io_list = list(info.get("investigating_officers", set()))
        cases_list = list(info.get("crime_numbers", set()))
        stations_list = list(info.get("stations", set()))

        nodes_output.append({
            "id": nid,
            "label": info.get("name", f"Accused #{nid}"),
            "name": info.get("name", f"Accused #{nid}"),
            "age": info.get("age"),
            "gender": info.get("gender", "Unknown"),
            "total_cases": len(info.get("cases", set())),
            "crime_committed": ", ".join(crime_types_list[:3]) if crime_types_list else "Penal Offence",
            "crime_numbers": cases_list[:3],
            "investigating_officer": io_list[0] if io_list else "Inspector Assigned",
            "investigating_officers": io_list[:3],
            "stations": stations_list[:3],
            "districts": list(info.get("districts", set()))[:3],
            "crime_types": crime_types_list[:3],
            "heinous_count": info.get("heinous_count", 0),
            "fraud_total": round(info.get("fraud_total", 0), 2),
            "degree_centrality": round(degree_cent.get(nid, 0), 4),
            "betweenness_centrality": round(betweenness_cent.get(nid, 0), 4),
            "community_id": node_community.get(nid, 0),
        })


    edges_output = []
    for u, v, data in G.edges(data=True):
        if u in top_node_ids and v in top_node_ids:
            edges_output.append({
                "source": u,
                "target": v,
                "weight": data.get("weight", 1.0),
                "relation": data.get("relation", "shared_case"),
                "shared_cases": data.get("shared_cases", 0),
                "shared_bank": data.get("shared_bank", 0),
            })

    # Compute total fraud
    total_fraud = sum(info.get("fraud_total", 0) for info in accused_info.values())

    # Top suspects for LLM summary
    top_suspects = sorted(nodes_output, key=lambda x: x["degree_centrality"], reverse=True)[:10]

    # Community summaries
    community_summaries = []
    for idx, members in enumerate(communities_list[:10]):
        member_names = [accused_info.get(m, {}).get("name", f"#{m}") for m in members[:5]]
        community_summaries.append(member_names)

    return {
        "total_nodes": len(G.nodes()),
        "total_edges": len(G.edges()),
        "total_communities": len(communities_list),
        "total_fraud_amount": round(total_fraud, 2),
        "nodes": nodes_output,
        "edges": edges_output,
        "communities": community_summaries,
        "top_suspects": top_suspects,
    }
