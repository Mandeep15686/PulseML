import axios from 'axios'
import type {
  Model, PredictionLog, DriftReport, Alert, Dashboard
} from '../types'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

// ── Models ────────────────────────────────────────────────────────────────────
export const modelsApi = {
  list: () => api.get<Model[]>('/models/').then(r => r.data),
  get:  (id: string) => api.get<Model>(`/models/${id}`).then(r => r.data),
  create: (data: Partial<Model>) => api.post<Model>('/models/', data).then(r => r.data),
  update: (id: string, data: Partial<Model>) =>
    api.patch<Model>(`/models/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/models/${id}`),
}

// ── Logs ──────────────────────────────────────────────────────────────────────
export const logsApi = {
  list:   (modelId: string) =>
    api.get<PredictionLog[]>(`/models/${modelId}/logs/`).then(r => r.data),
  upload: (modelId: string, data: any) =>
    api.post<PredictionLog>(`/models/${modelId}/logs/`, data).then(r => r.data),
  delete: (modelId: string, logId: string) =>
    api.delete(`/models/${modelId}/logs/${logId}`),
}

// ── Drift ─────────────────────────────────────────────────────────────────────
export const driftApi = {
  list: (modelId: string) =>
    api.get<DriftReport[]>(`/models/${modelId}/drift`).then(r => r.data),
  get:  (modelId: string, reportId: string) =>
    api.get<DriftReport>(`/models/${modelId}/drift/${reportId}`).then(r => r.data),
  trigger: (modelId: string, refWindow: string, tgtWindow: string) =>
    api.post<DriftReport>(
      `/models/${modelId}/drift`,
      null,
      { params: { reference_window: refWindow, target_window: tgtWindow } }
    ).then(r => r.data),
}

// ── Alerts ────────────────────────────────────────────────────────────────────
export const alertsApi = {
  listAll:    (resolved = false) =>
    api.get<Alert[]>('/alerts', { params: { resolved } }).then(r => r.data),
  listModel:  (modelId: string, resolved = false) =>
    api.get<Alert[]>(`/models/${modelId}/alerts`, { params: { resolved } }).then(r => r.data),
  resolve:    (alertId: string) =>
    api.patch<Alert>(`/alerts/${alertId}/resolve`).then(r => r.data),
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const dashboardApi = {
  get: () => api.get<Dashboard>('/dashboard').then(r => r.data),
}
