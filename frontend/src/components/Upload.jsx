import { useState, useCallback } from 'react'
import { Upload as UploadIcon, Shield, FileText, Users, AlertCircle, CheckCircle } from 'lucide-react'

const STAGES = [
  'Parsing chat...',
  'Filtering messages...',
  'Analyzing contributions...',
  'Building visualizations...',
]

export default function Upload({ onSuccess }) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [stage, setStage] = useState(0)
  const [preview, setPreview] = useState(null)

  const handleFile = (f) => {
    setError(null)
    if (!f || !f.name.endsWith('.txt')) {
      setError('Please upload a valid WhatsApp chat export (.txt) file.')
      setFile(null)
      setPreview(null)
      return
    }
    setFile(f)

    // Quick preview: count members
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target.result
      const lines = text.split('\n')
      const names = new Set()
      lines.forEach(line => {
        const m = line.match(/^\[?\d{1,2}\/\d{1,2}\/\d{2,4},?\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?\]?\s*-?\s*([^:]+):/)
        if (m) names.add(m[1].trim())
      })
      setPreview({
        name: f.name,
        size: (f.size / 1024).toFixed(1) + ' KB',
        members: names.size > 0 ? names.size : '?',
        lines: lines.length
      })
    }
    reader.readAsText(f)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    handleFile(f)
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setStage(0)

    try {
      // Stage 1: Upload + Parse
      const formData = new FormData()
      formData.append('file', file)
      setStage(0)
      const uploadRes = await fetch('http://localhost:8000/upload', { method: 'POST', body: formData })
      if (!uploadRes.ok) {
        const err = await uploadRes.json()
        throw new Error(err.detail || 'Upload failed')
      }
      const parsed = await uploadRes.json()
      setStage(1)

      await new Promise(r => setTimeout(r, 600))
      setStage(2)

      // Stage 2: Analyze
      const analyzeRes = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed),
      })
      if (!analyzeRes.ok) {
        const err = await analyzeRes.json()
        throw new Error(err.detail || 'Analysis failed')
      }
      const analysis = await analyzeRes.json()
      setStage(3)

      // Stage 3: Build AI RAG Index
      const initRes = await fetch('http://localhost:8000/init-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parsed_chat: parsed, analysis: analysis }),
      })
      if (!initRes.ok) {
        console.error('Failed to init AI session, but continuing anyway');
      }
      const initData = await initRes.ok ? await initRes.json() : { session_id: null };

      await new Promise(r => setTimeout(r, 500))
      onSuccess(parsed, analysis, initData.session_id)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary opacity-10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-purple-600 opacity-10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="text-center mb-10 animate-fade-in">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center glow-primary">
            <Users className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-4xl font-bold font-heading gradient-text">TeamLens</h1>
        </div>
        <p className="text-gray-400 text-lg max-w-md">
          AI-powered WhatsApp group chat contribution analyzer. See who really showed up.
        </p>

        {/* Privacy badge */}
        <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface border border-border text-sm text-gray-400">
          <Shield className="w-4 h-4 text-success" />
          Your data is never stored — cleared from memory after analysis
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`relative w-full max-w-xl glass p-10 rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer
          ${dragging ? 'border-primary glow-primary scale-105' : 'border-border hover:border-primary/50'}
          ${error ? 'border-danger' : ''}
        `}
        onClick={() => !loading && document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".txt"
          className="hidden"
          onChange={e => handleFile(e.target.files[0])}
        />

        {loading ? (
          <div className="flex flex-col items-center gap-6 py-4">
            <div className="relative w-16 h-16">
              <div className="w-16 h-16 rounded-full border-4 border-border animate-spin border-t-primary" />
            </div>
            <div className="text-center">
              <p className="text-accent font-semibold text-lg mb-3">{STAGES[stage]}</p>
              <div className="flex gap-2 justify-center">
                {STAGES.map((s, i) => (
                  <div
                    key={i}
                    className={`h-1.5 w-8 rounded-full transition-all duration-500 ${i <= stage ? 'bg-primary' : 'bg-border'}`}
                  />
                ))}
              </div>
            </div>
          </div>
        ) : preview ? (
          <div className="flex flex-col items-center gap-4 animate-fade-in">
            <CheckCircle className="w-12 h-12 text-success" />
            <div className="text-center">
              <p className="text-accent font-semibold text-lg">{preview.name}</p>
              <div className="flex gap-4 justify-center mt-2 text-sm text-gray-400">
                <span>📦 {preview.size}</span>
                <span>👥 ~{preview.members} members</span>
                <span>💬 {preview.lines} lines</span>
              </div>
            </div>
            <p className="text-xs text-gray-500">Click to choose a different file</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 text-center">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${dragging ? 'bg-primary scale-110' : 'bg-surface'}`}>
              <UploadIcon className={`w-8 h-8 ${dragging ? 'text-white' : 'text-primary'}`} />
            </div>
            <div>
              <p className="text-accent font-semibold text-lg">Drop your WhatsApp chat export here</p>
              <p className="text-gray-400 text-sm mt-1">or click to browse • .txt files only</p>
            </div>
            <div className="flex gap-2 flex-wrap justify-center text-xs text-gray-500">
              <span className="px-2 py-1 bg-surface rounded-full">Android format ✓</span>
              <span className="px-2 py-1 bg-surface rounded-full">iPhone format ✓</span>
              <span className="px-2 py-1 bg-surface rounded-full">Any group size ✓</span>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 flex items-center gap-2 text-danger text-sm animate-fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* How to export guide */}
      <div className="mt-6 glass p-5 rounded-xl w-full max-w-xl">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-sm font-semibold text-gray-300">How to export your WhatsApp chat</span>
        </div>
        <ol className="text-xs text-gray-400 space-y-1 list-decimal list-inside">
          <li>Open WhatsApp → Group Chat → ⋮ Menu (or swipe on iPhone)</li>
          <li>Tap <strong>"More"</strong> → <strong>"Export chat"</strong></li>
          <li>Choose <strong>"Without Media"</strong></li>
          <li>Save the .txt file and upload it here</li>
        </ol>
      </div>

      {/* Analyze Button */}
      {preview && !loading && (
        <button
          onClick={handleSubmit}
          className="mt-6 px-8 py-3 bg-primary hover:bg-indigo-500 text-white font-semibold rounded-xl transition-all duration-200 glow-primary hover:scale-105 animate-slide-up"
        >
          Analyze Chat ✨
        </button>
      )}
    </div>
  )
}
