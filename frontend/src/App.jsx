import { useState } from 'react'
import Upload from './components/Upload'
import Dashboard from './components/Dashboard'
import FloatingAssistant from './components/ai/FloatingAssistant'
import './index.css'

export default function App() {
  const [view, setView] = useState('upload') // 'upload' | 'dashboard'
  const [parsedData, setParsedData] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  const handleUploadSuccess = (parsed, analysis, aiSessionId) => {
    setParsedData(parsed)
    setAnalysisData(analysis)
    setSessionId(aiSessionId)
    setView('dashboard')
  }

  const handleReset = () => {
    setParsedData(null)
    setAnalysisData(null)
    setSessionId(null)
    setView('upload')
  }

  return (
    <div className="min-h-screen bg-bg text-accent">
      {view === 'upload' ? (
        <Upload onSuccess={handleUploadSuccess} />
      ) : (
        <Dashboard
          parsedData={parsedData}
          analysisData={analysisData}
          onReset={handleReset}
        />
      )}
      <FloatingAssistant sessionId={sessionId} isReady={view === 'dashboard'} />
    </div>
  )
}
