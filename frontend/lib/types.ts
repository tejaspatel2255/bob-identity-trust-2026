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

export interface Confidence {
  confidence_pct: number;
  confidence_label: 'HIGH' | 'MEDIUM' | 'LOW';
  reasoning: string;
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
  action: FrictionAction | string;
  timestamp: string;
  reviewed: boolean;
  review_outcome: string | null;
  confidence?: Confidence;
  event_data?: Record<string, any>;
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

export interface Persona {
  id: string;
  name: string;
  trustLevel: 'safe' | 'warning' | 'danger' | 'purple';
  description: string;
  entityType: 'CUSTOMER_SESSION' | 'EMPLOYEE_ACCESS';
  entityId: string;
  eventData: Record<string, any>;
}

export interface CorrelationEmployee {
  id: string;
  name: string;
  role: string;
  access_time: string;
  action_type: string;
}

export interface CorrelationCustomer {
  id: string;
  name: string;
  recovery_time: string;
  recovery_new_device: boolean;
}

export interface CorrelationAlert {
  type: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  employee: CorrelationEmployee;
  customer: CorrelationCustomer;
  minutes_apart: number;
  all_matches: Record<string, unknown>[];
}

export interface CorrelationResult {
  correlated: boolean;
  account_id: string;
  alert: CorrelationAlert | null;
  message?: string;
}

export interface ScanResult {
  total_correlated_accounts: number;
  alerts: Record<string, unknown>[];
}

export interface RiskHistoryPoint {
  timestamp: string;
  risk_score: number;
}

export interface RiskHistory {
  customer_id: string;
  history: RiskHistoryPoint[];
}
