import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, FileText, CheckCircle } from 'lucide-react'
import { modelsApi, logsApi } from '../api/client'

export function Upload() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { data: models = [] } = useQuery({ queryKey: ['models'], queryFn: modelsApi.list })

  const [modelId, setModelId] = useState('')
  const [windowLabel, setWindowLabel] = useState('')
  const [predictionsText, setPredictionsText] = useState('')
  const [labelsText, setLabelsText] = useState('')
  const [err, setErr] = useState('')
  const [success, setSuccess] = useState(false)

  const upload = useMutation({
    mutationFn: (data: any) => logsApi.upload(modelId, data),
    onSuccess: (log) => {
      qc.invalidateQueries({ queryKey: ['logs'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      setSuccess(true)
      setTimeout(() => navigate(`/models/${modelId}`), 1500)
    },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Upload failed'),
  })

  const parseFloats = (text: string): number[] =>
    text.split(/[\n,\s]+/).map(s => s.trim()).filter(Boolean).map(Number).filter(n => !isNaN(n))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErr('')
    const predictions = parseFloats(predictionsText)
    if (predictions.length === 0) { setErr('No valid predictions found.'); return }
    if (!modelId) { setErr('Select a model.'); return }
    if (!windowLabel) { setErr('Enter a window label.'); return }

    const labels = labelsText.trim() ? parseFloats(labelsText).map(Math.round) : undefined
    upload.mutate({ window_label: windowLabel, predictions, labels })
  }

  if (success) return (
    <div className="max-w-lg mx-auto px-4 py-24 text-center">
      <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
      <p className="text-white font-semibold text-lg">Upload successful!</p>
      <p className="text-gray-400 text-sm mt-1">Redirecting to model dashboard…</p>
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Prediction Log</h1>
        <p className="text-gray-400 text-sm mt-1">Upload a batch of predictions for drift monitoring.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
        {err && <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-lg">{err}</div>}

        <div>
          <label className="text-xs text-gray-400 font-medium block mb-1">Model *</label>
          <select value={modelId} onChange={e => setModelId(e.target.value)} required
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm">
            <option value="">Select a model…</option>
            {models.map(m => <option key={m.id} value={m.id}>{m.name} (v{m.version})</option>)}
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-400 font-medium block mb-1">Window Label *</label>
          <input value={windowLabel} onChange={e => setWindowLabel(e.target.value)} required
            placeholder="e.g. 2024-W01, batch-42, March-2024"
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500" />
        </div>

        <div>
          <label className="text-xs text-gray-400 font-medium block mb-1">
            Prediction Scores * <span className="text-gray-600">(values in [0,1], comma or newline separated)</span>
          </label>
          <textarea value={predictionsText} onChange={e => setPredictionsText(e.target.value)} required rows={5}
            placeholder="0.92, 0.14, 0.78, 0.33, 0.55 …"
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 font-mono resize-none" />
          <p className="text-xs text-gray-500 mt-1">{parseFloats(predictionsText).length} values detected</p>
        </div>

        <div>
          <label className="text-xs text-gray-400 font-medium block mb-1">
            Ground Truth Labels <span className="text-gray-600">(optional, 0 or 1 for classification)</span>
          </label>
          <textarea value={labelsText} onChange={e => setLabelsText(e.target.value)} rows={3}
            placeholder="1, 0, 1, 0, 1 …"
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 font-mono resize-none" />
        </div>

        <div className="bg-gray-800/50 rounded-lg p-4 flex gap-3">
          <FileText size={16} className="text-gray-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-gray-400">
            Drift analysis runs automatically when a second window is uploaded.
            You can also trigger it manually from the Model Detail page.
          </p>
        </div>

        <button type="submit" disabled={upload.isPending}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white py-2.5 rounded-lg font-medium transition-colors">
          <UploadIcon size={15} />
          {upload.isPending ? 'Uploading…' : 'Upload Log'}
        </button>
      </form>
    </div>
  )
}
