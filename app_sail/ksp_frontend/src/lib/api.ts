import { QueryResponse, NetworkGraphData, NetworkResponsePayload, GraphSummaryResponse, ZiaOcrResponse, AnalyticsResponsePayload } from "./types";



const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function sendQuery(query: string, sessionId: string = "default_session", userRole: string = "Analyst"): Promise<QueryResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: sessionId, user_role: userRole }),
    });
    return await res.json();
  } catch (e: any) {
    return {
      session_id: sessionId,
      answer: `❌ Connection Error: ${e.message}`,
      intent: "ERROR",
      data: [],
      explainable_ai: {
        sql_executed: "",
        was_redacted: false,
        rows_touched: 0,
        execution_time_seconds: 0,
      },
      error: e.message,
    };
  }
}

export async function fetchNetworkPayload(params: {
  district?: string;
  crime_type?: string;
  date_range?: string;
  start_date?: string;
  end_date?: string;
  min_link_strength?: number;
  node_types?: string[];
}): Promise<NetworkResponsePayload> {
  const urlParams = new URLSearchParams();
  if (params.district) urlParams.append("district", params.district);
  if (params.crime_type) urlParams.append("crime_type", params.crime_type);
  if (params.date_range) urlParams.append("date_range", params.date_range);
  if (params.start_date) urlParams.append("start_date", params.start_date);
  if (params.end_date) urlParams.append("end_date", params.end_date);
  if (params.min_link_strength) urlParams.append("min_link_strength", String(params.min_link_strength));
  if (params.node_types && params.node_types.length > 0) {
    urlParams.append("node_types", params.node_types.join(","));
  }

  try {
    const res = await fetch(`${API_BASE}/api/network?${urlParams.toString()}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error("fetchNetworkPayload error:", e);
    return {
      total_nodes_before_cap: 0,
      nodes_rendered: 0,
      total_edges: 0,
      capped: false,
      filters_applied: {
        district: params.district || "all",
        crime_type: params.crime_type || "all",
        date_range: params.date_range || "90",
        min_link_strength: params.min_link_strength || 1,
        node_types: params.node_types || ["accused", "victim", "location", "financial"]
      },
      nodes: [],
      edges: []
    };
  }

}

export async function fetchNetworkOptions(): Promise<{ districts: string[]; crime_types: string[] }> {
  try {
    const res = await fetch(`${API_BASE}/api/network/options`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error("fetchNetworkOptions error:", e);
    return { districts: [], crime_types: [] };
  }
}

export async function fetchEntityProfile(entityId: string, entityType: string): Promise<any> {
  try {
    const params = new URLSearchParams({ entity_id: entityId, entity_type: entityType });
    const res = await fetch(`${API_BASE}/api/network/profile?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error("fetchEntityProfile error:", e);
    return {
      status: "error",
      entity_id: entityId,
      entity_type: entityType,
      label: `Entity #${entityId}`,
      risk_level: "STANDARD RECORD",
      total_cases: 0,
      attributes: {},
      cases: [],
      recommendations: ["**CCTNS Real-Time Alert:** Intelligence tracking active."]
    };
  }
}

export async function fetchAnalyticsSummary(
  district: string = "all",
  crimeType: string = "all",
  dateRange: string = "365",
  selectedYear: string = "all"
): Promise<AnalyticsResponsePayload | null> {
  try {
    const params = new URLSearchParams({
      district,
      crime_type: crimeType,
      date_range: dateRange,
      selected_year: selectedYear
    });
    const res = await fetch(`${API_BASE}/api/analytics/summary?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error("fetchAnalyticsSummary error:", e);
    return null;
  }
}





export async function fetchNetworkGraph(district?: string, crimeHeadId?: number, minConnections: number = 1): Promise<NetworkGraphData> {

  const params = new URLSearchParams({ min_connections: String(minConnections) });
  if (district) params.append("district", district);
  if (crimeHeadId) params.append("crime_head_id", String(crimeHeadId));

  const res = await fetch(`${API_BASE}/api/graph/rebuild?${params.toString()}`, {
    method: "POST",
  });
  const data = await res.json();
  return data.graph || data;
}

export async function fetchGraphSummary(district?: string, crimeHeadId?: number, minConnections: number = 1): Promise<GraphSummaryResponse> {
  const params = new URLSearchParams({ min_connections: String(minConnections) });
  if (district) params.append("district", district);
  if (crimeHeadId) params.append("crime_head_id", String(crimeHeadId));

  const res = await fetch(`${API_BASE}/api/graph/summary?${params.toString()}`, {
    method: "POST",
  });
  return await res.json();
}

export async function generatePdfReport(title: string, markdownContent: string): Promise<{ success?: boolean; filename?: string; download_url?: string; size_bytes?: number; error?: string }> {
  const res = await fetch(`${API_BASE}/api/report/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, markdown_content: markdownContent }),
  });
  const data = await res.json();
  if (data.download_url && !data.download_url.startsWith("http")) {
    data.download_url = `${API_BASE}${data.download_url}`;
  }
  return data;
}

export async function exportDocxReport(title: string, markdownContent: string): Promise<{ success?: boolean; filename?: string; download_url?: string; size_bytes?: number; error?: string }> {
  const res = await fetch(`${API_BASE}/api/report/export_docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, markdown_content: markdownContent }),
  });
  const data = await res.json();
  if (data.download_url && !data.download_url.startsWith("http")) {
    data.download_url = `${API_BASE}${data.download_url}`;
  }
  return data;
}


export async function summarizeZiaOcr(text: string): Promise<ZiaOcrResponse> {
  const res = await fetch(`${API_BASE}/api/zia/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return await res.json();
}

