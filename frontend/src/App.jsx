import { useState } from 'react'
import Upload from './components/Upload'
import Dashboard from './components/Dashboard'
import './index.css'

export default function App() {
  const [view, setView] = useState('upload') // 'upload' | 'dashboard'
  const [parsedData, setParsedData] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)

  const handleUploadSuccess = (parsed, analysis) => {
    setParsedData(parsed)
    setAnalysisData(analysis)
    setView('dashboard')
  }

  const handleReset = () => {
    setParsedData(null)
    setAnalysisData(null)
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
    </div>
  )
}
