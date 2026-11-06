import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Trash2, ChevronRight } from 'lucide-react'
import { modelsApi } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import type { TaskType } from '../types'

export function Models() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', version: '1.0.0', description: '', task_type: 'binary_classification' as TaskType, feature_names: '' })
  const [err, setErr] = useState('')

  const { data: models = [], isLoading } = useQuery({ queryKey: ['models'], queryFn: modelsApi.list })

  const create = useMutation({
    mutationFn: (d: any) => modelsApi.create(d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['models'] }); setShowForm(false); setErr('') },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Error creating model'),
  })

  const del = useMutation({
    mutationFn: modelsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['models'] }),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    create.mutate({
      name: form.name, version: form.version,
      description: form.description || null, task_type: form.task_type,
      feature_names: form.feature_names.split(',').map(s => s.trim()).filter(Boolean),
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Models</h1>
          <p className="text-gray-400 text-sm mt-1">Manage registered ML models.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <Plus size={15} /> Register Model
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
          <h2 className="font-semibold text-white">Register New Model</h2>
          {err && <p className="text-red-400 text-sm">{err}</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Name *" value={form.name} onChange={v => setForm(f => ({...f, name: v}))} placeholder="my_fraud_model" required />
            <Field label="Version" value={form.version} onChange={v => setForm(f => ({...f, version: v}))} />
            <div>
              <label className="text-xs text-gray-400 font-medium block mb-1">Task Type *</label>
              <select value={form.task_type} onChange={e => setForm(f => ({...f, task_type: e.target.value as TaskType}))}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm">
                <option value="binary_classification">Binary Classification</option>
                <option value="multiclass_classification">Multiclass Classification</option>
                <option value="regression">Regression</option>
              </select>
            </div>
            <Field label="Feature Names (comma-separated)" value={form.feature_names} onChange={v => setForm(f => ({...f, feature_names: v}))} placeholder="age, income, score" />
            <div className="md:col-span-2">
              <Field label="Description" value={form.description} onChange={v => setForm(f => ({...f, description: v}))} />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={create.isPending}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              {create.isPending ? 'Registering…' : 'Register'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white px-4 py-2 text-sm transition-colors">Cancel</button>
          </div>
        </form>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading…</div>
        ) : models.length === 0 ? (
          <div className="p-12 text-center text-gray-500">No models yet. Register your first model above.</div>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Name</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Type</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Features</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Active</th>
              <th className="px-4 py-3"></th>
            </tr></thead>
            <tbody>
              {models.map(m => (
                <tr key={m.id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                  <td className="px-4 py-3">
                    <Link to={`/models/${m.id}`} className="font-medium text-white hover:text-blue-400 flex items-center gap-1">
                      {m.name} <ChevronRight size={12} className="text-gray-500"/>
                    </Link>
                    <p className="text-xs text-gray-500">v{m.version}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-400 capitalize text-xs">{m.task_type.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{m.feature_names.length} features</td>
                  <td className="px-4 py-3"><StatusBadge status={m.is_active ? 'ok' : 'unknown'} /></td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => { if (confirm('Delete model and all its data?')) del.mutate(m.id) }}
                      className="text-gray-500 hover:text-red-400 p-1 rounded transition-colors"><Trash2 size={14} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function Field({ label, value, onChange, placeholder, required }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; required?: boolean }) {
  return (
    <div>
      <label className="text-xs text-gray-400 font-medium block mb-1">{label}</label>
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} required={required}
        className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500" />
    </div>
  )
}
