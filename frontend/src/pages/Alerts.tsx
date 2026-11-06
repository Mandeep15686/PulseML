import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Bell, CheckCircle } from 'lucide-react'
import { alertsApi } from '../api/client'
import { SeverityBadge } from '../components/StatusBadge'
import { formatDistanceToNow } from 'date-fns'

export function Alerts() {
  const qc = useQueryClient()
  const [resolved, setResolved] = useState(false)
  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['allAlerts', resolved],
    queryFn: () => alertsApi.listAll(resolved),
  })
  const resolve = useMutation({
    mutationFn: alertsApi.resolve,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['allAlerts'] }),
  })

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-gray-400 text-sm mt-1">Drift and performance degradation alerts.</p>
        </div>
        <div className="flex gap-2">
          {(['open','resolved'] as const).map(tab => (
            <button key={tab} onClick={() => setResolved(tab === 'resolved')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                (resolved ? 'resolved' : 'open') === tab
                  ? 'bg-blue-500/15 text-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-400 p-8 text-center">Loading…</div>
      ) : alerts.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Bell size={40} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400">{resolved ? 'No resolved alerts.' : 'No open alerts — all models healthy!'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map(a => (
            <div key={a.id} className={`bg-gray-900 border rounded-xl px-5 py-4 flex items-start gap-4 ${
              a.severity === 'high' ? 'border-red-500/30' : a.severity === 'medium' ? 'border-amber-500/30' : 'border-gray-800'
            }`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <SeverityBadge severity={a.severity} />
                  <span className="text-xs text-gray-400">{a.drift_type.replace(/_/g,' ')}</span>
                  {a.feature && <span className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{a.feature}</span>}
                </div>
                <p className="text-sm text-gray-200">{a.message}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatDistanceToNow(new Date(a.created_at), { addSuffix: true })}
                </p>
              </div>
              {!a.is_resolved && (
                <button onClick={() => resolve.mutate(a.id)} title="Resolve"
                  className="text-gray-500 hover:text-emerald-400 transition-colors flex-shrink-0">
                  <CheckCircle size={18} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
