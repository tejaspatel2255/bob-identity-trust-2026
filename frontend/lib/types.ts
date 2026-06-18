export interface NodeProperties {
  id?: string;
  name?: string;
  role?: string;
  access_level?: string;
  department?: string;
  fingerprint?: string;
  os?: string;
  browser?: string;
  is_new?: boolean;
  trust_score?: number;
  timestamp?: string;
  ip?: string;
  city?: string;
  geolocation_lat?: number;
  geolocation_lng?: number;
  duration_seconds?: number;
  sim_swap_flag?: boolean;
  label?: string;
  typing_cadence_wpm?: number;
  swipe_speed_px_per_sec?: number;
  tap_pressure_avg?: number;
  balance_tier?: string;
  account_type?: string;
  is_frozen?: boolean;
  bank_ifsc?: string;
  is_first_time?: boolean;
  amount?: number;
  [key: string]: any;
}

export interface NodeModel {
  id: string;
  type: string; // "Customer" | "Device" | "Session" | "Employee" | "Account" | "Beneficiary"
  properties: NodeProperties;
}

export interface EdgeProperties {
  timestamp?: string;
  action_type?: string;
  outside_hours?: boolean;
  amount?: number;
  geovelocity_jump_km?: number;
  [key: string]: any;
}

export interface EdgeModel {
  source: string;
  target: string;
  type: string; // "OWNS" | "LOGGED_IN_FROM" | "INITIATED" | "USED_DEVICE" | "TRANSFERRED_TO" | "ACCESSED" | "VIEWED_KYC" | "RECOVERY_ATTEMPTED"
  properties: EdgeProperties;
}

export interface SubgraphResponse {
  nodes: NodeModel[];
  edges: EdgeModel[];
}

export interface FrictionAction {
  action: "SILENT_PASS" | "STEP_UP_AUTH" | "HARD_BLOCK";
  level: "LOW" | "MEDIUM" | "HIGH";
  color: "green" | "amber" | "red";
  message: string | null;
  route_to: string | null;
}

export interface ShapAttribution {
  feature: string;
  contribution: number;
}

export interface RiskEvent {
  id: string;
  entity_id: string;
  entity_type: string; // "CUSTOMER_SESSION" | "EMPLOYEE_ACCESS"
  risk_score: number;
  shap_attributions: ShapAttribution[];
  explanation: string;
  provider_used: string; // "llama-3.3-70b" | "gemini-flash" | "gpt-4o-mini" | "template"
  model_id: string;
  fallback_used: boolean;
  action: string; // "SILENT_PASS" | "STEP_UP_AUTH" | "HARD_BLOCK"
  action_level: string; // "LOW" | "MEDIUM" | "HIGH"
  timestamp: string;
  reviewed: boolean;
  review_outcome: string | null; // "FALSE_POSITIVE" | "CONFIRMED_FRAUD"
}

export interface RiskScoreResponse {
  entity_id: string;
  entity_type: string;
  risk_score: number;
  shap_attributions: ShapAttribution[];
  explanation: string;
  provider_used: string;
  fallback_used: boolean;
  model_id: string;
  action: FrictionAction;
  timestamp: string;
}

export interface HealthResponse {
  neo4j_connected: boolean;
  total_nodes: number;
  total_edges: number;
  flagged_last_24h: number;
  model_version: string;
}

export interface Persona {
  id: string;
  name: string;
  avatarUrl?: string;
  trustLevel: "safe" | "warning" | "danger" | "purple";
  description: string;
  entityType: string;
  entityId: string;
  eventData: Record<string, any>;
}
