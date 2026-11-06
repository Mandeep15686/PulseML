import type { DriftStatus, AlertSeverity } from '../types'

const statusStyles: Record<DriftStatus, string> = {
  ok:       'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  warning:  'bg-amber-500/15   text-amber-400   border-amber-500/30',
  critical: 'bg-red-500/15     text-red-400     border-red-500/30',
  unknown:  'bg-gray-500/15    text-gray-400    border-gray-500/30',
}
const statusDots: Record<DriftStatus, string> = {
  ok: 'bg-emerald-400', warning: 'bg-amber-400', critical: 'bg-red-400', unknown: 'bg-gray-400',
}

export function StatusBadge({ status }: { status: DriftStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${statusStyles[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${statusDots[status]} ${status === 'critical' ? 'animate-pulse' : ''}`} />
      {status.toUpperCase()}
    </span>
  )
}

const sevStyles: Record<AlertSeverity, string> = {
  low:    'bg-blue-500/15   text-blue-400   border-blue-500/30',
  medium: 'bg-amber-500/15  text-amber-400  border-amber-500/30',
  high:   'bg-red-500/15    text-red-400    border-red-500/30',
}

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${sevStyles[severity]}`}>
      {severity.toUpperCase()}
    </span>
  )
}
