export interface ShapAttribution {
  feature: string;
  contribution: number;
}

export interface FrictionAction {
  action: 'SILENT_PASS' | 'STEP_UP_AUTH' | 'HARD_BLOCK';
  level: 'LOW' | 'MEDIUM' | 'HIGH';
  color: 'green' | 'amber' | 'red';
  message: string | null;
  route_to: string | null;
}

export interface RiskEvent {
  id: string;
  entity_id: string;
  entity_type: 'CUSTOMER_SESSION' | 'EMPLOYEE_ACCESS';
  customer_id: string | null;
  risk_score: number;
  shap_attributions: ShapAttribution[];
  explanation: string;
  provider_used: string;
  model_id: string;
  fallback_used: boolean;
  action: FrictionAction;
  timestamp: string;
  reviewed: boolean;
  review_outcome: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface HealthStatus {
  neo4j_connected: boolean;
  total_nodes: number;
  total_edges: number;
  flagged_last_24h: number;
  model_version: string;
  supabase_connected: boolean;
}
