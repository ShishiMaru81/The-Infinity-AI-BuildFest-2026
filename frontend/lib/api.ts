import { API_URL } from "./utils";

export interface Incident {
  id: number;
  incident_type: string;
  priority: string;
  threat_level: string;
  status: string;
  alert_status: string;
  description: string;
  location: string;
  latitude: number;
  longitude: number;
  confidence: number;
  detected_objects: string;
  scene_analysis: string;
  recommended_action: string;
  agent_reasoning: string;
  source: string;
  created_at: string;
}

export interface Stats {
  incidents_today: number;
  critical_today: number;
  active_cameras: number;
  system_status: string;
}

export interface AppSettings {
  alert_mode: string;
  police_number: string;
  app_mode: string;
  hospitals: unknown[];
  detection_confidence_threshold: number;
  detection_consecutive_frames: number;
  frame_fps: number;
  real_dispatch_cooldown_sec: number;
  test_email: string;
  fallback_address: string;
}

export interface DispatchPayload {
  incident_id?: number;
  threat_type: string;
  confidence: number;
  location: string;
  latitude: number;
  longitude: number;
  description: string;
  snapshot_b64?: string;
  mode?: string;
}

export interface DispatchResult {
  status: string;
  mode?: string;
  email?: { status: string };
  sms?: { status: string };
  call?: { status: string };
  log_id?: string;
  email_to?: string;
  reason?: string;
  cooldown_remaining_sec?: number;
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/api/stats`);
  return res.json();
}

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_URL}/api/incidents`);
  return res.json();
}

export async function acknowledgeIncident(id: number) {
  return fetch(`${API_URL}/api/incidents/${id}/acknowledge`, { method: "POST" });
}

export async function uploadVideo(file: File, fps: number, lat: number, lng: number) {
  const form = new FormData();
  form.append("file", file);
  form.append("fps", String(fps));
  form.append("lat", String(lat));
  form.append("lng", String(lng));
  const res = await fetch(`${API_URL}/api/video/upload`, { method: "POST", body: form });
  return res.json();
}

export async function getVideoJob(jobId: string) {
  const res = await fetch(`${API_URL}/api/video/job/${jobId}`);
  return res.json();
}

export async function fetchSettings(): Promise<AppSettings> {
  const res = await fetch(`${API_URL}/api/settings`);
  return res.json();
}

export async function updateSettings(data: Partial<AppSettings>) {
  const res = await fetch(`${API_URL}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function dispatchEmergency(data: DispatchPayload): Promise<DispatchResult> {
  const res = await fetch(`${API_URL}/api/dispatch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function fetchHealth(): Promise<{ app_mode: string }> {
  const res = await fetch(`${API_URL}/api/health`);
  return res.json();
}
