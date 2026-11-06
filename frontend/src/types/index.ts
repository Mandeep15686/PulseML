export type TaskType = 'binary_classification' | 'multiclass_classification' | 'regression'
export type DriftStatus = 'ok' | 'warning' | 'critical' | 'unknown'
export type AlertSeverity = 'low' | 'medium' | 'high'

export interface Model {
  id: string
  name: string
  version: string
  description: string | null
  task_type: TaskType
  feature_names: string[]
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface PredictionLog {
  id: string
  model_id: string
  window_label: string
  logged_at: string
  n_samples: number
  features_stats: Record<string, FeatureStats>
  prediction_dist: Record<string, number>
  label_dist: Record<string, number> | null
  performance: Record<string, number> | null
}

export interface FeatureStats {
  mean: number; std: number; min: number; max: number
  p25: number; p50: number; p75: number; count: number
}

export interface DriftReport {
  id: string
  model_id: string
  reference_window: string
  target_window: string
  generated_at: string
  overall_status: DriftStatus
  feature_drift: Record<string, any>
  prediction_drift: Record<string, any>
  performance_drift: Record<string, any> | null
  summary: string | null
}

export interface Alert {
  id: string
  model_id: string
  severity: AlertSeverity
  message: string
  drift_type: string
  feature: string | null
  created_at: string
  is_resolved: boolean
  resolved_at: string | null
}

export interface ModelSummary {
  model: Model
  n_logs: number
  n_reports: number
  n_open_alerts: number
  latest_status: DriftStatus
  latest_window: string | null
}

export interface Dashboard {
  total_models: number
  active_models: number
  total_alerts: number
  open_alerts: number
  critical_models: number
  models: ModelSummary[]
}
