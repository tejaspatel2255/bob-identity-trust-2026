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
    apiFetch('/risk/score', { method: 'POST', body: JSON.stringify(body) }),

  getSubgraph: (customerId: string) =>
    apiFetch(`/graph/subgraph/${customerId}`),

  getFullGraph: () =>
    apiFetch('/graph/all'),

  getHealth: () =>
    apiFetch('/health'),

  getEvents: () =>
    apiFetch<any[]>('/risk/events'),

  getEvent: (eventId: string) =>
    apiFetch(`/risk/events/${eventId}`),

  reviewEvent: (eventId: string, reviewed: boolean, review_outcome: string) =>
    apiFetch(`/risk/events/${eventId}`, {
      method: 'PATCH',
      body: JSON.stringify({ reviewed, review_outcome }),
    }),
};
