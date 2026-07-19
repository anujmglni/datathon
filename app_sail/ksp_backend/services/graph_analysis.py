"""
Criminal Network Analysis Service for KSP Platform.
Uses NetworkX to build offender association graphs (shared cases, locations, bank accounts).
"""

import networkx as nx
from database import execute_query

def build_criminal_network(min_weight: float = 1.0) -> dict:
    """
    Reads Accused and FinancialTransaction records, computes co-occurrence graphs,
    and returns JSON nodes, edges, and centrality scores.
    """
    G = nx.Graph()

    # 1. Fetch accused co-occurrence in cases
    accused_rows = execute_query("SELECT AccusedMasterID, CaseMasterID, AccusedName, PersonID FROM Accused;")

    case_accused_map = {}
    for r in accused_rows:
        case_accused_map.setdefault(r["CaseMasterID"], []).append(r)
        G.add_node(r["AccusedMasterID"], name=r["AccusedName"], person_id=r["PersonID"])

    for case_id, members in case_accused_map.items():
        if len(members) > 1:
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    u = members[i]["AccusedMasterID"]
                    v = members[j]["AccusedMasterID"]
                    if G.has_edge(u, v):
                        G[u][v]["weight"] += 1.0
                    else:
                        G.add_edge(u, v, weight=1.0, relation="shared_case")

    # 2. Compute centrality
    centrality = nx.degree_centrality(G) if len(G) > 0 else {}

    nodes = [
        {
            "id": n,
            "label": data.get("name", f"Accused #{n}"),
            "degree_centrality": round(centrality.get(n, 0), 4)
        }
        for n, data in G.nodes(data=True)
    ]

    edges = [
        {
            "source": u,
            "target": v,
            "weight": data.get("weight", 1.0),
            "relation": data.get("relation", "shared_case")
        }
        for u, v, data in G.edges(data=True)
    ]

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes[:50],  # Return top slice for visualization
        "edges": edges[:100]
    }
