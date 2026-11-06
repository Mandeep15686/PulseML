import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, RefreshCw, Zap } from 'lucide-react'
import { modelsApi, logsApi, driftApi, alertsApi } from '../api/client'
import { StatusBadge, SeverityBadge } from '../components/StatusBadge'
import { DriftChart } from '../components/DriftChart'
import { PredDistChart } from '../components/PredDistChart'
import { formatDistanceToNow } from 'date-fns'

export function ModelDetail() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [activeReport, setActiveReport] = useState<string | null>(null)
  const [triggerRef, setTriggerRef] = useState('')
  const [triggerTgt, setTriggerTgt] = useState('')
  const [triggerErr, setTriggerErr] = useState('')

  const { data: model } = useQuery({ queryKey: ['model', id], queryFn: () => modelsApi.get(id!) })
  const { data: logs = [] } = useQuery({ queryKey: ['logs', id], queryFn: () => logsApi.list(id!) })
  const { data: reports = [] } = useQuery({ queryKey: ['reports', id], queryFn: () => driftApi.list(id!) })
  const { data: alerts = [] } = useQuery({ queryKey: ['alerts', id], queryFn: () => alertsApi.listModel(id!) })

  const triggerDrift = useMutation({
    mutationFn: () => driftApi.trigger(id!, triggerRef, triggerTgt),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['reports', id] })
      qc.invalidateQueries({ queryKey: ['alerts', id] })
      setActiveReport(r.id)
      setTriggerErr('')
    },
    onError: (e: any) => setTriggerErr(e.response?.data?.detail ?? 'Drift analysis failed'),
  })

  const resolveAlert = useMutation({
    mutationFn: alertsApi.resolve,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts', id] }),
  })

  // Build drift timeline
  const driftTimeline = reports.slice().reverse().map(r => {
    const psi = r.prediction_drift?.psi?.psi ?? null
    const ks  = r.prediction_drift?.ks_test?.statistic ?? null
    const acc = r.performance_drift?.metrics?.accuracy?.current ?? null
    return { window: r.target_window, psi, ks, accuracy: acc }
  })

  const selectedReport = reports.find(r => r.id === activeReport) ?? reports[0]

  if (!model) return <div className="p-8 text-gray-400">Loading…</div>

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/models" className="text-gray-400 hover:text-white transition-colors"><ArrowLeft size={18} /></Link>
        <div>
          <h1 className="text-2xl font-bold text-white">{model.name}</h1>
          <p className="text-gray-400 text-sm">v{model.version} · {model.task_type.replace(/_/g,' ')} · {model.feature_names.length} features</p>
        </div>
      </div>

      {/* Drift Timeline */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><RefreshCw size={14}/> Drift Timeline</h2>
        <DriftChart data={driftTimeline} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prediction Logs */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">Prediction Windows ({logs.length})</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {logs.length === 0 && <p className="text-gray-500 text-xs">No logs uploaded yet.</p>}
            {logs.map(log => (
              <div key={log.id} className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2">
                <div>
                  <p className="text-xs font-medium text-white">{log.window_label}</p>
                  <p className="text-xs text-gray-500">{log.n_samples.toLocaleString()} samples</p>
                </div>
                {log.performance?.accuracy != null && (
                  <span className="text-xs text-emerald-400 font-medium">
                    ACC {(log.performance.accuracy * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Trigger Drift */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Zap size={14}/> Run Drift Analysis</h2>
          {triggerErr && <p className="text-red-400 text-xs mb-2">{triggerErr}</p>}
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Reference Window</label>
              <select value={triggerRef} onChange={e => setTriggerRef(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded px-2 py-1.5 text-sm">
                <option value="">Select…</option>
                {logs.map(l => <option key={l.id} value={l.window_label}>{l.window_label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Target Window</label>
              <select value={triggerTgt} onChange={e => setTriggerTgt(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded px-2 py-1.5 text-sm">
                <option value="">Select…</option>
                {logs.map(l => <option key={l.id} value={l.window_label}>{l.window_label}</option>)}
              </select>
            </div>
            <button
              onClick={() => triggerDrift.mutate()}
              disabled={!triggerRef || !triggerTgt || triggerDrift.isPending}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white py-2 rounded-lg text-sm font-medium transition-colors">
              {triggerDrift.isPending ? 'Analysing…' : 'Run Analysis'}
            </button>
          </div>
        </div>

        {/* Open Alerts */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">Open Alerts ({alerts.length})</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {alerts.length === 0 && <p className="text-gray-500 text-xs">No open alerts. All clear!</p>}
            {alerts.map(a => (
              <div key={a.id} className="bg-gray-800/50 rounded-lg px-3 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <SeverityBadge severity={a.severity} />
                  <span className="text-xs text-gray-400">{a.drift_type.replace('_',' ')}</span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">{a.message}</p>
                <button onClick={() => resolveAlert.mutate(a.id)}
                  className="text-xs text-blue-400 hover:text-blue-300 mt-1 transition-colors">
                  Resolve →
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Latest Drift Report */}
      {selectedReport && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">
              Latest Report: {selectedReport.reference_window} → {selectedReport.target_window}
            </h2>
            <StatusBadge status={selectedReport.overall_status} />
          </div>
          {selectedReport.summary && (
            <p className="text-xs text-gray-400 mb-4 font-mono bg-gray-800/50 p-3 rounded-lg">{selectedReport.summary}</p>
          )}
          <div>
            <p className="text-xs font-medium text-gray-400 mb-2">Prediction Distribution Comparison</p>
            {logs.length >= 2 && (
              <PredDistChart
                reference={logs.find(l => l.window_label === selectedReport.reference_window)?.prediction_dist ?? {}}
                current={logs.find(l => l.window_label === selectedReport.target_window)?.prediction_dist ?? {}}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
