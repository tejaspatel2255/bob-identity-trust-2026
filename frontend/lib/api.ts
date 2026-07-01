import { RiskEvent, GraphData, HealthStatus } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  scoreEvent: (body: object) =>
    apiFetch<any>('/risk/score', { method: 'POST', body: JSON.stringify(body) }),

  getSubgraph: (customerId: string) =>
    apiFetch<GraphData>(`/graph/subgraph/${customerId}`),

  getFullGraph: () =>
    apiFetch<GraphData>('/graph/all'),

  getHealth: () =>
    apiFetch<HealthStatus>('/health'),

  getEvents: () =>
    apiFetch<RiskEvent[]>('/risk/events'),

  getEvent: (eventId: string) =>
    apiFetch<RiskEvent>(`/risk/events/${eventId}`),

  reviewEvent: (eventId: string, reviewed: boolean, review_outcome: string) =>
    apiFetch<any>(`/risk/events/${eventId}`, {
      method: 'PATCH',
      body: JSON.stringify({ reviewed, review_outcome }),
    }),

  downloadCasePdf: (eventId: string): void => {
    window.open(`${BASE_URL}/risk/events/${eventId}/pdf`, '_blank');
  },
};
