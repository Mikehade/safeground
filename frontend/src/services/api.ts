import axios from 'axios';
import type {
  IncidentReport,
  ScoutRequest,
  ScoutResponse,
  SafetyResource,
  FeedbackRequest,
  IncidentMarker,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120_000, // agent calls can take a while
});

export const incidentApi = {
  report: (data: IncidentReport) =>
    api.post<{ receipt_token: string; message: string }>('/incidents/report', data),

  checkStatus: (token: string) =>
    api.post<{ found: boolean; status?: string; incident_type?: string; created_at?: string }>(
      '/incidents/status',
      { token }
    ),

  getRecent: (region?: string, limit = 50) =>
    api.get<IncidentMarker[]>('/incidents/recent', { params: { region, limit } }),
};

/* ── Scout streaming ── */

export type StreamEvent =
  | { type: 'status'; message: string }
  | { type: 'tool'; name: string; message: string }
  | { type: 'token'; text: string }
  | { type: 'advisory'; text: string }
  | { type: 'done'; tool_calls: number }
  | { type: 'error'; message: string };

/**
 * Stream scout analysis via NDJSON.
 * Calls `onEvent` for every parsed line — tool progress, tokens, done/error.
 */
export async function streamScout(
  data: ScoutRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/scout/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    signal,
  });

  if (!resp.ok) {
    throw new Error(`Scout stream failed: ${resp.status}`);
  }

  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Split on newlines — each line is one JSON event
    const lines = buffer.split('\n');
    buffer = lines.pop()!; // keep incomplete trailing line

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        onEvent(JSON.parse(trimmed) as StreamEvent);
      } catch {
        // skip malformed lines
      }
    }
  }

  // Flush remaining buffer
  if (buffer.trim()) {
    try {
      onEvent(JSON.parse(buffer.trim()) as StreamEvent);
    } catch {
      // skip
    }
  }
}

export const scoutApi = {
  analyze: (data: ScoutRequest) => api.post<ScoutResponse>('/scout/analyze', data),
};

export const resourceApi = {
  findNearby: (lat: number, lng: number, type?: string) =>
    api.get<SafetyResource[]>('/resources/nearby', {
      params: { lat, lng, resource_type: type, radius_km: 15 },
    }),
};

export const feedbackApi = {
  submit: (data: FeedbackRequest) => api.post('/feedback/', data),
};
