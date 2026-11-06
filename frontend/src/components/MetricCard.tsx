import type { ReactNode } from 'react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: ReactNode
  accent?: 'default' | 'warning' | 'danger' | 'success'
}

const accents = {
  default: 'text-blue-400',
  warning: 'text-amber-400',
  danger:  'text-red-400',
  success: 'text-emerald-400',
}

export function MetricCard({ label, value, sub, icon, accent = 'default' }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start gap-4">
      {icon && (
        <div className="p-2 rounded-lg bg-gray-800 text-gray-400 flex-shrink-0">
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{label}</p>
        <p className={`text-2xl font-bold ${accents[accent]}`}>{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
