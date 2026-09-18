import axios from 'axios';
import type {
  IncidentReport,
  ScoutRequest,
  ScoutResponse,
  SafetyResource,
  FeedbackRequest,
  IncidentMarker,
} from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
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
