import {
  HealthResponse,
  SubgraphResponse,
  RiskScoreResponse,
  RiskEvent,
  FrictionAction
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class to handle API failures with status codes
 */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

/**
 * Generic fetch wrapper with standard error handling
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMsg = errBody.detail;
      }
    } catch {
      // Ignore JSON parse errors on non-json replies
    }
    throw new ApiError(errorMsg, response.status);
  }

  return response.json() as Promise<T>;
}

/**
 * System Health
 */
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

/**
 * Retrieve the entire graph (Global View)
 */
export async function getGlobalGraph(): Promise<SubgraphResponse> {
  return request<SubgraphResponse>("/graph/all");
}

/**
 * Retrieve 2-hop subgraph for a customer
 */
export async function getCustomerSubgraph(customerId: string): Promise<SubgraphResponse> {
  return request<SubgraphResponse>(`/graph/subgraph/${customerId}`);
}

/**
 * Retrieve employee activity
 */
export async function getEmployeeActivity(employeeId: string): Promise<any> {
  return request<any>(`/graph/employee/${employeeId}`);
}

/**
 * Score a risk event using rules and fallback LLM explanation
 */
export async function scoreRisk(payload: {
  entity_type: string;
  entity_id: string;
  event_data: Record<string, any>;
}): Promise<RiskScoreResponse> {
  return request<RiskScoreResponse>("/risk/score", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve logged risk events from history (in-memory or Supabase)
 */
export async function getRiskEvents(): Promise<RiskEvent[]> {
  return request<RiskEvent[]>("/risk/events");
}

/**
 * Update the review status of an ingestion alert
 */
export async function reviewRiskEvent(
  eventId: string,
  payload: { reviewed: boolean; review_outcome: string }
): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(`/risk/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
