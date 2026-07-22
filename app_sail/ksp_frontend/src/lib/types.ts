export interface DatabaseRecord {
  CaseMasterID?: number;
  CrimeNo?: number;
  CrimeRegisteredDate?: string;
  BriefFacts?: string;
  DistrictName?: string;
  CrimeGroupName?: string;
  [key: string]: unknown;
}

export interface ExplainableAI {
  sql_executed: string;
  was_redacted: boolean;
  rows_touched: number;
  execution_time_seconds: number;
  slots_active?: Record<string, unknown>;
}

export interface QueryResponse {
  session_id: string;
  answer: string;
  intent: string;
  data: DatabaseRecord[];
  explainable_ai: ExplainableAI;
  error?: string;
}

export interface NetworkNode {
  id: number;
  label: string;
  name: string;
  age?: number;
  gender?: string;
  total_cases: number;
  crime_committed?: string;
  crime_numbers?: string[];
  investigating_officer?: string;
  districts: string[];
  crime_types: string[];
  heinous_count: number;
  fraud_total: number;
  degree_centrality: number;
  betweenness_centrality: number;
  community_id: number;
}


export interface NetworkEdge {
  source: number;
  target: number;
  weight: number;
  relation: string;
  shared_cases: number;
  shared_bank: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "accused" | "victim" | "location" | "financial";
  color: string;
  linked_case_count: number;
  cases: number[];
  district?: string;
  station?: string;
  risk_indicator?: string;
  degree?: number;
  details?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  relation: string;
  evidence: {
    cases: number[];
    transactions?: number[];
    description: string;
  };
}

export interface NetworkResponsePayload {
  total_nodes_before_cap: number;
  nodes_rendered: number;
  total_edges: number;
  capped: boolean;
  filters_applied: {
    district: string;
    crime_type: string;
    date_range: string;
    min_link_strength: number;
    node_types: string[];
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NetworkGraphData {
  total_nodes: number;
  total_edges: number;
  total_communities: number;
  total_fraud_amount: number;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  communities: string[][];
  top_suspects: NetworkNode[];
}


export interface GraphSummaryResponse {
  status: string;
  summary: string;
  stats: {
    total_nodes: number;
    total_edges: number;
    total_communities: number;
    total_fraud_amount: number;
  };
}

export interface ZiaOcrResponse {
  status: string;
  service: string;
  executive_summary: string;
  extracted_entities: {
    ipc_sections: string[];
    jurisdictions: string[];
    word_count: number;
    character_count: number;
  };
  zia_confidence_score: number;
}

export interface AnalyticsChartBlock<T = any> {
  data: T[];
  links?: any[];
  description: string;
  how_to_read?: string;
}


export interface AnalyticsResponsePayload {
  status: string;
  filters_applied: {
    district: string;
    crime_type: string;
    date_range: string;
  };
  heatmap_district_month: AnalyticsChartBlock;
  heatmap_crime_timeofday: AnalyticsChartBlock;
  line_crime_trends: AnalyticsChartBlock;
  bar_top_offenses: AnalyticsChartBlock;
  choropleth_district_map: AnalyticsChartBlock;
  donut_case_status: AnalyticsChartBlock;
  financial_crime_summary: AnalyticsChartBlock;
  sociological_correlation: AnalyticsChartBlock;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  result?: QueryResponse;
  timestamp: Date;
}

