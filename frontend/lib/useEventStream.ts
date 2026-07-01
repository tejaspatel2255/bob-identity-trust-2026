'use client';
import { useEffect, useRef, useState } from 'react';
import type { RiskEvent } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useEventStream(maxEvents: number = 50) {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Fetch initial history
    fetch(`${BASE_URL}/risk/events`)
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error('Failed to fetch initial events');
      })
      .then((data) => {
        setEvents(data.slice(0, maxEvents));
      })
      .catch((err) => console.error('Error fetching initial events:', err));

    const es = new EventSource(`${BASE_URL}/stream/events`);
    sourceRef.current = es;

    es.addEventListener('connected', () => setConnected(true));

    es.addEventListener('risk_event', (e: MessageEvent) => {
      try {
        const newEvent: RiskEvent = JSON.parse(e.data);
        setEvents((prev) => {
          // Prevent duplicates if already fetched
          if (prev.some((x) => x.id === newEvent.id)) return prev;
          return [newEvent, ...prev].slice(0, maxEvents);
        });
      } catch (err) {
        console.error('Failed to parse SSE event', err);
      }
    });

    es.onerror = () => setConnected(false);

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, [maxEvents]);

  return { events, connected };
}
