import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, Database, TrendingDown } from 'lucide-react'
import { dashboardApi } from '../api/client'
import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'
import { formatDistanceToNow } from 'date-fns'

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
    refetchInterval: 15_000,
  })

  if (isLoading) return <PageLoader />
  if (error || !data) return <Error msg="Failed to load dashboard." />

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time overview of all monitored models.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard label="Total Models"   value={data.total_models}   icon={<Database size={16}/>} />
        <MetricCard label="Active Models"  value={data.active_models}  icon={<Activity size={16}/>} accent="success" />
        <MetricCard label="Open Alerts"    value={data.open_alerts}    icon={<AlertTriangle size={16}/>} accent={data.open_alerts > 0 ? 'warning' : 'default'} />
        <MetricCard label="Critical"       value={data.critical_models} icon={<TrendingDown size={16}/>} accent={data.critical_models > 0 ? 'danger' : 'default'} />
        <MetricCard label="Total Alerts"   value={data.total_alerts}   />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Models</h2>
        {data.models.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
            <Database size={40} className="text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No models registered yet.</p>
            <Link to="/models" className="mt-4 inline-block bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg transition-colors">
              Register Model
            </Link>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Model</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Type</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Logs</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Alerts</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Last Window</th>
                </tr>
              </thead>
              <tbody>
                {data.models.map(({ model, n_logs, n_reports, n_open_alerts, latest_status, latest_window }) => (
                  <tr key={model.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                    <td className="px-4 py-3">
                      <Link to={`/models/${model.id}`} className="font-medium text-white hover:text-blue-400 transition-colors">
                        {model.name}
                      </Link>
                      <p className="text-xs text-gray-500">v{model.version}</p>
                    </td>
                    <td className="px-4 py-3 text-gray-400 capitalize">{model.task_type.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3"><StatusBadge status={latest_status} /></td>
                    <td className="px-4 py-3 text-gray-300">{n_logs}</td>
                    <td className="px-4 py-3">
                      <span className={n_open_alerts > 0 ? 'text-amber-400 font-semibold' : 'text-gray-500'}>{n_open_alerts}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{latest_window ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function PageLoader() {
  return <div className="flex items-center justify-center h-64 text-gray-400">Loading…</div>
}
function Error({ msg }: { msg: string }) {
  return <div className="flex items-center justify-center h-64 text-red-400">{msg}</div>
}
