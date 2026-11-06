import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

interface Props {
  reference: Record<string, number>
  current:   Record<string, number>
}

export function PredDistChart({ reference, current }: Props) {
  const buckets = Array.from(new Set([...Object.keys(reference), ...Object.keys(current)])).sort()
  const data = buckets.map(b => ({
    bucket:    b,
    reference: reference[b] ?? 0,
    current:   current[b]   ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="bucket" tick={{ fill: '#6b7280', fontSize: 9 }} angle={-30} textAnchor="end" />
        <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
        <Bar dataKey="reference" name="Reference" fill="#3b82f6" fillOpacity={0.7} radius={[2,2,0,0]} />
        <Bar dataKey="current"   name="Current"   fill="#8b5cf6" fillOpacity={0.7} radius={[2,2,0,0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
