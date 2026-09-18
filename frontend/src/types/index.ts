export interface LocationInput {
  lat?: number;
  lng?: number;
  name?: string;
}

export interface ScoutRequest {
  origin: LocationInput;
  destination: LocationInput;
  current_hour: number;
}

export interface ScoutResponse {
  advisory: string;
  routes: RouteData[];
  tool_calls: number;
}

export interface RouteData {
  index: number;
  distance_km: number;
  duration_min: number;
  risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  advisory: string;
  geometry: LatLng[];
  incidents: IncidentMarker[];
}

export interface LatLng {
  lat: number;
  lng: number;
}

export interface IncidentReport {
  incident_type: string;
  latitude: number;
  longitude: number;
  description?: string;
  city?: string;
  region?: string;
  severity?: number;
}

export interface IncidentMarker {
  type: string;
  lat: number;
  lng: number;
  severity: number;
  city?: string;
  created_at: string;
  hours_ago?: number;
}

export interface SafetyResource {
  id: string;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  phone?: string;
  address?: string;
  operating_hours?: string;
}

export interface FeedbackRequest {
  assessment_id?: string;
  helpful: boolean;
  context?: string;
}

export type Tab = 'scout' | 'report' | 'resources' | 'status';
