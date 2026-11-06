import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

interface DriftPoint {
  window: string
  psi: number | null
  ks: number | null
  accuracy: number | null
}

interface Props { data: DriftPoint[] }

export function DriftChart({ data }: Props) {
  if (!data.length) return (
    <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
      No drift data yet — upload more prediction windows.
    </div>
  )

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="window" tick={{ fill: '#6b7280', fontSize: 11 }} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={[0, 'auto']} />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
          labelStyle={{ color: '#f3f4f6' }}
        />
        <ReferenceLine y={0.2} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'PSI warn', fill: '#f59e0b', fontSize: 10 }} />
        <Line type="monotone" dataKey="psi" name="PSI" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: '#3b82f6' }} connectNulls />
        <Line type="monotone" dataKey="ks"  name="KS"  stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3, fill: '#8b5cf6' }} connectNulls />
        <Line type="monotone" dataKey="accuracy" name="Accuracy" stroke="#10b981" strokeWidth={2} dot={{ r: 3, fill: '#10b981' }} connectNulls strokeDasharray="6 2" />
      </LineChart>
    </ResponsiveContainer>
  )
}
