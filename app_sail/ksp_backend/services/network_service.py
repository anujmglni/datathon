"""
Dedicated Network Graph Service for KSP Crime Intelligence Platform.
Computes multi-entity graph nodes (Accused, Victim, Location, Financial Account)
and evidence-backed edges (Accused-Accused co-accused, Accused-Location, 
Accused-Financial, Victim-Accused) with strict server-side filtering and node caps.
"""

import logging
from typing import Dict, List, Any, Set
from database import execute_query

logger = logging.getLogger(__name__)


def fetch_filter_options() -> Dict[str, List[str]]:
    """Fetch distinct districts and crime major heads for frontend dropdowns."""
    districts_res = execute_query("SELECT DISTINCT districtname FROM district WHERE districtname IS NOT NULL AND districtname != '' ORDER BY districtname;")
    districts = [r["districtname"] for r in districts_res if r.get("districtname")]

    crime_types_res = execute_query("SELECT DISTINCT crimegroupname FROM crimehead WHERE crimegroupname IS NOT NULL AND crimegroupname != '' ORDER BY crimegroupname;")
    crime_types = [r["crimegroupname"] for r in crime_types_res if r.get("crimegroupname")]

    return {
        "districts": districts,
        "crime_types": crime_types
    }



def get_network_graph(
    district: str = "all",
    crime_type: str = "all",
    date_range: str = "90",
    start_date: str = None,
    end_date: str = None,
    min_link_strength: int = 1,
    node_types: List[str] = None
) -> Dict[str, Any]:

    """
    Builds nodes and edges for the filtered Crime Intelligence Network Graph.
    Enforces server-side node cap of 300 top-connected entities.
    """
    if node_types is None:
        node_types = ["accused", "victim", "location", "financial"]
    else:
        node_types = [t.lower().strip() for t in node_types if t.strip()]

    min_link_strength = max(1, int(min_link_strength))

    # 1. Build CaseMaster Filter Query
    where_clauses = ["1=1"]
    params = []

    if district and district.lower() != "all":
        where_clauses.append("d.districtname ILIKE %s")
        params.append(f"%{district}%")

    if crime_type and crime_type.lower() != "all":
        where_clauses.append("(ch.crimegroupname ILIKE %s OR c.brieffacts ILIKE %s)")
        params.extend([f"%{crime_type}%", f"%{crime_type}%"])

    # Date range relative to max registration date in dataset
    if date_range == "30":
        where_clauses.append("c.crimeregistereddate::date >= (SELECT MAX(crimeregistereddate::date) - INTERVAL '30 days' FROM casemaster)")
    elif date_range == "90":
        where_clauses.append("c.crimeregistereddate::date >= (SELECT MAX(crimeregistereddate::date) - INTERVAL '90 days' FROM casemaster)")
    elif date_range == "365":
        where_clauses.append("c.crimeregistereddate::date >= (SELECT MAX(crimeregistereddate::date) - INTERVAL '365 days' FROM casemaster)")
    elif date_range == "custom" and start_date and end_date:
        where_clauses.append("c.crimeregistereddate::date BETWEEN %s::date AND %s::date")
        params.extend([start_date, end_date])
    # default fallback to 90 days if unspecified or invalid
    elif date_range not in ["all", "365", "30", "90"]:
        where_clauses.append("c.crimeregistereddate::date >= (SELECT MAX(crimeregistereddate::date) - INTERVAL '90 days' FROM casemaster)")


    where_sql = " AND ".join(where_clauses)

    # Fetch matching CaseMaster IDs
    cases_sql = f"""
        SELECT 
            c.casemasterid AS CaseMasterID,
            c.crimeno AS CrimeNo,
            c.crimeregistereddate AS CrimeRegisteredDate,
            c.policestationid AS PoliceStationID,
            u.unitname AS StationName,
            d.districtname AS DistrictName,
            ch.crimegroupname AS CrimeGroupName
        FROM casemaster c
        LEFT JOIN unit u ON c.policestationid = u.unitid
        LEFT JOIN district d ON u.districtid = d.districtid
        LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
        WHERE {where_sql}
        ORDER BY c.casemasterid DESC
        LIMIT 1500;
    """

    filtered_cases = execute_query(cases_sql, tuple(params) if params else ())
    if not filtered_cases:
        return {
            "total_nodes_before_cap": 0,
            "nodes_rendered": 0,
            "total_edges": 0,
            "capped": False,
            "filters_applied": {
                "district": district,
                "crime_type": crime_type,
                "date_range": date_range,
                "min_link_strength": min_link_strength,
                "node_types": node_types
            },
            "nodes": [],
            "edges": []
        }

    case_ids = [r.get("CaseMasterID") or r.get("casemasterid") for r in filtered_cases]
    case_ids = [c for c in case_ids if c is not None]
    if not case_ids:
        return {
            "total_nodes_before_cap": 0,
            "nodes_rendered": 0,
            "total_edges": 0,
            "capped": False,
            "filters_applied": {
                "district": district,
                "crime_type": crime_type,
                "date_range": date_range,
                "min_link_strength": min_link_strength,
                "node_types": node_types
            },
            "nodes": [],
            "edges": []
        }

    case_map = {(r.get("CaseMasterID") or r.get("casemasterid")): r for r in filtered_cases}
    case_id_tuples = tuple(case_ids)

    # 2. Fetch Accused for these cases
    accused_rows = []
    if "accused" in node_types or "location" in node_types or "financial" in node_types or "victim" in node_types:
        acc_sql = """
            SELECT 
                a.accusedmasterid AS AccusedMasterID,
                a.casemasterid AS CaseMasterID,
                a.accusedname AS AccusedName,
                a.ageyear AS AgeYear,
                a.genderid AS GenderID,
                a.personid AS PersonID
            FROM accused a
            WHERE a.casemasterid IN %s;
        """
        accused_rows = execute_query(acc_sql, (case_id_tuples,))

    # 3. Fetch Victims for these cases
    victim_rows = []
    if "victim" in node_types:
        vic_sql = """
            SELECT 
                v.victimmasterid AS VictimMasterID,
                v.casemasterid AS CaseMasterID,
                v.victimname AS VictimName,
                v.ageyear AS AgeYear,
                v.genderid AS GenderID
            FROM victim v
            WHERE v.casemasterid IN %s;
        """
        victim_rows = execute_query(vic_sql, (case_id_tuples,))

    # 4. Fetch Financial Transactions for these cases
    fin_rows = []
    if "financial" in node_types:
        fin_sql = """
            SELECT 
                ft.transactionid AS TransactionID,
                ft.casemasterid AS CaseMasterID,
                ft.accusedmasterid AS AccusedMasterID,
                ft.fraudtype AS FraudType,
                ft.amountlostinr AS AmountLostINR,
                ft.bankaccountlast4 AS BankAccountLast4,
                ft.status AS Status
            FROM financialtransaction ft
            WHERE ft.casemasterid IN %s AND ft.bankaccountlast4 IS NOT NULL;
        """
        fin_rows = execute_query(fin_sql, (case_id_tuples,))


    # Node and Edge Stores
    nodes_dict: Dict[str, Dict[str, Any]] = {}
    raw_edges: Dict[str, Dict[str, Any]] = {}

    # Build Accused Nodes
    for r in accused_rows:
        aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
        cid = r.get("CaseMasterID") or r.get("casemasterid")
        name = r.get("AccusedName") or r.get("accusedname") or f"Accused #{aid}"
        age = r.get("AgeYear") or r.get("ageyear")
        gender = r.get("GenderID") or r.get("genderid")
        person_id = r.get("PersonID") or r.get("personid")
        c_info = case_map.get(cid, {})

        if "accused" in node_types and aid:
            nid = f"accused_{aid}"
            if nid not in nodes_dict:
                nodes_dict[nid] = {
                    "id": nid,
                    "label": name,
                    "type": "accused",
                    "color": "#ef4444",
                    "linked_case_count": 0,
                    "cases": set(),
                    "district": c_info.get("DistrictName") or c_info.get("districtname") or "Unknown",
                    "station": c_info.get("StationName") or c_info.get("stationname") or "Unknown",
                    "details": {
                        "AccusedMasterID": aid,
                        "PersonID": person_id,
                        "Age": age,
                        "Gender": "Male" if gender == 1 else ("Female" if gender == 2 else "Other")
                    }
                }
            nodes_dict[nid]["cases"].add(cid)
            nodes_dict[nid]["linked_case_count"] = len(nodes_dict[nid]["cases"])

    # Build Victim Nodes
    for r in victim_rows:
        vid = r.get("VictimMasterID") or r.get("victimmasterid")
        cid = r.get("CaseMasterID") or r.get("casemasterid")
        vname = r.get("VictimName") or r.get("victimname") or f"Victim #{vid}"
        age = r.get("AgeYear") or r.get("ageyear")
        gender = r.get("GenderID") or r.get("genderid")
        c_info = case_map.get(cid, {})

        if "victim" in node_types and vid:
            nid = f"victim_{vid}"
            if nid not in nodes_dict:
                nodes_dict[nid] = {
                    "id": nid,
                    "label": vname,
                    "type": "victim",
                    "color": "#3b82f6",
                    "linked_case_count": 0,
                    "cases": set(),
                    "district": c_info.get("DistrictName") or c_info.get("districtname") or "Unknown",
                    "station": c_info.get("StationName") or c_info.get("stationname") or "Unknown",
                    "details": {
                        "VictimMasterID": vid,
                        "Age": age,
                        "Gender": "Male" if gender == 1 else ("Female" if gender == 2 else "Other")
                    }
                }
            nodes_dict[nid]["cases"].add(cid)
            nodes_dict[nid]["linked_case_count"] = len(nodes_dict[nid]["cases"])

    # Build Location Nodes (from CaseMaster)
    if "location" in node_types:
        for r in filtered_cases:
            unit_id = r.get("PoliceStationID") or r.get("policestationid")
            station_name = r.get("StationName") or r.get("stationname") or f"Station #{unit_id}"
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            dist = r.get("DistrictName") or r.get("districtname") or "Unknown"

            if unit_id and cid:
                nid = f"location_{unit_id}"
                if nid not in nodes_dict:
                    nodes_dict[nid] = {
                        "id": nid,
                        "label": station_name,
                        "type": "location",
                        "color": "#22c55e",
                        "linked_case_count": 0,
                        "cases": set(),
                        "district": dist,
                        "station": station_name,
                        "details": {
                            "UnitID": unit_id,
                            "District": dist
                        }
                    }
                nodes_dict[nid]["cases"].add(cid)
                nodes_dict[nid]["linked_case_count"] = len(nodes_dict[nid]["cases"])

    # Build Financial Account Nodes
    if "financial" in node_types:
        for r in fin_rows:
            last4 = r.get("BankAccountLast4") or r.get("bankaccountlast4")
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            fraud_type = r.get("FraudType") or r.get("fraudtype")
            amount = r.get("AmountLostINR") or r.get("amountlostinr")
            c_info = case_map.get(cid, {})

            if last4 and cid:
                nid = f"financial_{last4}"
                if nid not in nodes_dict:
                    nodes_dict[nid] = {
                        "id": nid,
                        "label": f"Account *{last4}",
                        "type": "financial",
                        "color": "#f59e0b",
                        "linked_case_count": 0,
                        "cases": set(),
                        "district": c_info.get("DistrictName") or c_info.get("districtname") or "Unknown",
                        "station": c_info.get("StationName") or c_info.get("stationname") or "Unknown",
                        "details": {
                            "BankAccountLast4": last4,
                            "FraudType": fraud_type,
                            "AmountLostINR": float(amount) if amount else 0.0
                        }
                    }
                nodes_dict[nid]["cases"].add(cid)
                nodes_dict[nid]["linked_case_count"] = len(nodes_dict[nid]["cases"])

    # --- EDGES GENERATION ---

    # 1. Accused ↔ Accused (Co-accused on same CaseMasterID)
    if "accused" in node_types:
        case_to_accused: Dict[int, List[int]] = {}
        for r in accused_rows:
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
            if cid and aid:
                case_to_accused.setdefault(cid, []).append(aid)

        for cid, acc_list in case_to_accused.items():
            acc_list = sorted(list(set(acc_list)))
            for i in range(len(acc_list)):
                for j in range(i + 1, len(acc_list)):
                    a1, a2 = acc_list[i], acc_list[j]
                    src, tgt = f"accused_{a1}", f"accused_{a2}"
                    if src in nodes_dict and tgt in nodes_dict:
                        edge_id = f"e_{src}_{tgt}"
                        if edge_id not in raw_edges:
                            raw_edges[edge_id] = {
                                "id": edge_id,
                                "source": src,
                                "target": tgt,
                                "weight": 0,
                                "relation": "Co-Accused on Case",
                                "cases": set(),
                                "evidence_type": "CaseMasterID"
                            }
                        raw_edges[edge_id]["weight"] += 1
                        raw_edges[edge_id]["cases"].add(cid)

    # 2. Accused ↔ Location (via CaseMaster PoliceStationID)
    if "accused" in node_types and "location" in node_types:
        for r in accused_rows:
            aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            unit_id = case_map.get(cid, {}).get("PoliceStationID") or case_map.get(cid, {}).get("policestationid")
            if aid and unit_id:
                src, tgt = f"accused_{aid}", f"location_{unit_id}"
                if src in nodes_dict and tgt in nodes_dict:
                    edge_id = f"e_{src}_{tgt}"
                    if edge_id not in raw_edges:
                        raw_edges[edge_id] = {
                            "id": edge_id,
                            "source": src,
                            "target": tgt,
                            "weight": 0,
                            "relation": "Registered / Arrested at Station",
                            "cases": set(),
                            "evidence_type": "CaseMasterID / PoliceStationID"
                        }
                    raw_edges[edge_id]["weight"] += 1
                    raw_edges[edge_id]["cases"].add(cid)

    # 3. Accused ↔ Financial Account (via FinancialTransaction)
    if "accused" in node_types and "financial" in node_types:
        for r in fin_rows:
            aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
            last4 = r.get("BankAccountLast4") or r.get("bankaccountlast4")
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            tid = r.get("TransactionID") or r.get("transactionid")
            if aid and last4:
                src, tgt = f"accused_{aid}", f"financial_{last4}"
                if src in nodes_dict and tgt in nodes_dict:
                    edge_id = f"e_{src}_{tgt}"
                    if edge_id not in raw_edges:
                        raw_edges[edge_id] = {
                            "id": edge_id,
                            "source": src,
                            "target": tgt,
                            "weight": 0,
                            "relation": "Linked Financial Account",
                            "cases": set(),
                            "transactions": set(),
                            "evidence_type": "TransactionID"
                        }
                    raw_edges[edge_id]["weight"] += 1
                    raw_edges[edge_id]["cases"].add(cid)
                    if "transactions" in raw_edges[edge_id] and tid:
                        raw_edges[edge_id]["transactions"].add(tid)

    # 4. Victim ↔ Accused (via shared CaseMasterID)
    if "victim" in node_types and "accused" in node_types:
        case_to_victims: Dict[int, List[int]] = {}
        for r in victim_rows:
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            vid = r.get("VictimMasterID") or r.get("victimmasterid")
            if cid and vid:
                case_to_victims.setdefault(cid, []).append(vid)

        for r in accused_rows:
            cid = r.get("CaseMasterID") or r.get("casemasterid")
            aid = r.get("AccusedMasterID") or r.get("accusedmasterid")
            if cid and aid and cid in case_to_victims:
                for vid in case_to_victims[cid]:
                    src, tgt = f"victim_{vid}", f"accused_{aid}"
                    if src in nodes_dict and tgt in nodes_dict:
                        edge_id = f"e_{src}_{tgt}"
                        if edge_id not in raw_edges:
                            raw_edges[edge_id] = {
                                "id": edge_id,
                                "source": src,
                                "target": tgt,
                                "weight": 0,
                                "relation": "Victim-Offender Case Link",
                                "cases": set(),
                                "evidence_type": "CaseMasterID"
                            }
                        raw_edges[edge_id]["weight"] += 1
                        raw_edges[edge_id]["cases"].add(cid)


    # --- FILTER EDGES BY MIN_LINK_STRENGTH ---
    filtered_edges = []
    connected_node_ids: Set[str] = set()

    for e in raw_edges.values():
        if e["weight"] >= min_link_strength:
            cases_list = list(e["cases"])
            trans_list = list(e.get("transactions", []))
            
            # Format Explainable AI evidence string
            ev_desc = f"Verified evidence linkage: {e['relation']} across {len(cases_list)} case(s) ({', '.join(f'#{c}' for c in cases_list[:5])})"
            if trans_list:
                ev_desc += f" & {len(trans_list)} transaction(s) ({', '.join(f'Txn#{t}' for t in trans_list[:5])})"

            filtered_edges.append({
                "id": e["id"],
                "source": e["source"],
                "target": e["target"],
                "weight": e["weight"],
                "relation": e["relation"],
                "evidence": {
                    "cases": cases_list,
                    "transactions": trans_list,
                    "description": ev_desc
                }
            })
            connected_node_ids.add(e["source"])
            connected_node_ids.add(e["target"])

    # Filter nodes to keep only nodes with degree >= 1 or in connected set
    active_nodes = [n for nid, n in nodes_dict.items() if nid in connected_node_ids]

    # Calculate degree for degree-based ranking
    node_degree: Dict[str, int] = {}
    for e in filtered_edges:
        node_degree[e["source"]] = node_degree.get(e["source"], 0) + e["weight"]
        node_degree[e["target"]] = node_degree.get(e["target"], 0) + e["weight"]

    for n in active_nodes:
        n["degree"] = node_degree.get(n["id"], 0)
        n["cases"] = list(n["cases"])
        
        # Risk Indicator computation
        cases_cnt = n["linked_case_count"]
        if n["type"] == "accused":
            n["risk_indicator"] = "CRITICAL (High Recidivism)" if cases_cnt >= 3 else ("HIGH (Repeat Offenses)" if cases_cnt >= 2 else "MODERATE")
        elif n["type"] == "financial":
            n["risk_indicator"] = "HIGH RISK (Mule Account)" if cases_cnt >= 2 else "SUSPECT ACCOUNT"
        elif n["type"] == "location":
            n["risk_indicator"] = "HOTSPOT STATION" if cases_cnt >= 5 else "ACTIVE JURISDICTION"
        else:
            n["risk_indicator"] = "PROTECTED VICTIM PROFILE"

    # Sort nodes by degree descending
    active_nodes.sort(key=lambda x: x["degree"], reverse=True)

    total_before_cap = len(active_nodes)
    capped = False

    # Server-side hard cap of 300 nodes
    if len(active_nodes) > 300:
        capped = True
        active_nodes = active_nodes[:300]
        rendered_ids = {n["id"] for n in active_nodes}
        filtered_edges = [e for e in filtered_edges if e["source"] in rendered_ids and e["target"] in rendered_ids]

    return {
        "total_nodes_before_cap": total_before_cap,
        "nodes_rendered": len(active_nodes),
        "total_edges": len(filtered_edges),
        "capped": capped,
        "filters_applied": {
            "district": district,
            "crime_type": crime_type,
            "date_range": date_range,
            "min_link_strength": min_link_strength,
            "node_types": node_types
        },
        "nodes": active_nodes,
        "edges": filtered_edges
    }


def get_entity_dossier_profile(entity_id: str, entity_type: str = "accused") -> Dict[str, Any]:
    """
    Fetches full case history, jurisdiction details, and offender dossier records
    for the requested entity (accused, victim, location, financial).
    """
    if not entity_id:
        return {"status": "error", "message": "Missing entity_id"}

    raw_id = entity_id.split("_")[-1]

    cases = []
    entity_name = f"Entity ({entity_id})"
    attributes = {}

    if entity_type == "accused":
        # Fetch accused details
        acc_info = execute_query("SELECT * FROM accused WHERE accusedmasterid = %s OR personid = %s LIMIT 1", (raw_id if raw_id.isdigit() else 0, str(raw_id)))
        if acc_info:
            r = acc_info[0]
            entity_name = r.get("accusedname") or f"Accused #{r.get('accusedmasterid')}"
            attributes = {
                "AccusedMasterID": r.get("accusedmasterid"),
                "PersonID": r.get("personid"),
                "Age": r.get("ageyear"),
                "Gender": "Male" if r.get("genderid") == 1 else ("Female" if r.get("genderid") == 2 else "Other")
            }

        # Fetch all linked cases
        cases_sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
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
            WHERE a.accusedmasterid = %s OR a.personid = %s
            ORDER BY c.casemasterid DESC;
        """
        cases = execute_query(cases_sql, (raw_id if raw_id.isdigit() else 0, str(raw_id)))

    elif entity_type == "victim":
        vic_info = execute_query("SELECT * FROM victim WHERE victimmasterid = %s LIMIT 1", (raw_id if raw_id.isdigit() else 0,))
        if vic_info:
            r = vic_info[0]
            entity_name = r.get("victimname") or f"Victim #{r.get('victimmasterid')}"
            attributes = {
                "VictimMasterID": r.get("victimmasterid"),
                "Age": r.get("ageyear"),
                "Gender": "Male" if r.get("genderid") == 1 else ("Female" if r.get("genderid") == 2 else "Other")
            }

        cases_sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
                d.districtname AS DistrictName,
                u.unitname AS StationName,
                ch.crimegroupname AS CrimeGroupName
            FROM victim v
            JOIN casemaster c ON v.casemasterid = c.casemasterid
            LEFT JOIN unit u ON c.policestationid = u.unitid
            LEFT JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            WHERE v.victimmasterid = %s
            ORDER BY c.casemasterid DESC;
        """
        cases = execute_query(cases_sql, (raw_id if raw_id.isdigit() else 0,))

    elif entity_type == "financial":
        entity_name = f"Account *{raw_id}"
        attributes = {"BankAccountLast4": raw_id}

        cases_sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
                d.districtname AS DistrictName,
                u.unitname AS StationName,
                ch.crimegroupname AS CrimeGroupName,
                ft.fraudtype AS FraudType,
                ft.amountlostinr AS AmountLostINR
            FROM financialtransaction ft
            JOIN casemaster c ON ft.casemasterid = c.casemasterid
            LEFT JOIN unit u ON c.policestationid = u.unitid
            LEFT JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            WHERE ft.bankaccountlast4 = %s
            ORDER BY c.casemasterid DESC;
        """
        cases = execute_query(cases_sql, (int(raw_id) if raw_id.isdigit() else 0,))


    elif entity_type == "location":
        unit_info = execute_query("SELECT * FROM unit WHERE unitid = %s LIMIT 1", (raw_id if raw_id.isdigit() else 0,))
        if unit_info:
            r = unit_info[0]
            entity_name = r.get("unitname") or f"Station #{r.get('unitid')}"
            attributes = {"UnitID": r.get("unitid")}

        cases_sql = """
            SELECT 
                c.casemasterid AS CaseMasterID,
                c.crimeno AS CrimeNo,
                c.crimeregistereddate AS CrimeRegisteredDate,
                c.brieffacts AS BriefFacts,
                d.districtname AS DistrictName,
                u.unitname AS StationName,
                ch.crimegroupname AS CrimeGroupName
            FROM casemaster c
            LEFT JOIN unit u ON c.policestationid = u.unitid
            LEFT JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            WHERE c.policestationid = %s
            ORDER BY c.casemasterid DESC
            LIMIT 50;
        """
        cases = execute_query(cases_sql, (raw_id if raw_id.isdigit() else 0,))

    return {
        "status": "success",
        "entity_id": entity_id,
        "entity_type": entity_type,
        "label": entity_name,
        "risk_level": "HIGH RISK / RECIDIVIST" if len(cases) >= 2 else "STANDARD RECORD",
        "total_cases": len(cases),
        "attributes": attributes,
        "cases": cases
    }

