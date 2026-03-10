import { useState, useCallback, useEffect } from 'react'
import PatientIntake from './components/PatientIntake'
import AnalysisResult from './components/AnalysisResult'
import SettingsPanel from './components/SettingsPanel'
import AboutPanel from './components/AboutPanel'
import './App.css'

// Use Vercel environment variable if deployed, otherwise fallback to local backend test port
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [activeTab, setActiveTab] = useState('intake')
  const [loading, setLoading] = useState(false)
  const [loadingText, setLoadingText] = useState('')
  const [toast, setToast] = useState(null)
  const [modelReady, setModelReady] = useState(false)

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState(null)
  const [heatmapImage, setHeatmapImage] = useState(null)
  const [showHeatmap, setShowHeatmap] = useState(false)

  // Settings
  const [settings, setSettings] = useState({
    showHeatmap: false,
  })

  // ── Splash screen: poll /health until model is ready ───────────
  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      while (!cancelled) {
        try {
          const res = await fetch(`${API_BASE}/health`)
          const data = await res.json()
          if (data.model_loaded) {
            setModelReady(true)
            return
          }
        } catch {
          // Server not up yet
        }
        await new Promise(r => setTimeout(r, 1000))
      }
    }
    poll()
    return () => { cancelled = true }
  }, [])

  const showToast = useCallback((message, type = 'error') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  // ── Run analysis ──────────────────────────────────────────────
  const handleAnalyze = useCallback(async (imageFile, age, site) => {
    setLoading(true)
    setLoadingText('Running AI analysis...')
    setHeatmapImage(null)
    setShowHeatmap(false)

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('age', age)
      formData.append('site', site)

      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Analysis failed')
      }

      const data = await res.json()
      setAnalysisResult({
        visImg: data.vis_img_b64,
        results: data.results,
        seeDoctor: data.see_doctor,
        numLesions: data.num_lesions,
        age,
        site,
        timestamp: new Date(),
      })
      setActiveTab('results')
      showToast('Analysis complete!', 'success')
    } catch (err) {
      showToast(err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  // ── Toggle heatmap ────────────────────────────────────────────
  const handleToggleHeatmap = useCallback(async () => {
    if (showHeatmap) {
      setShowHeatmap(false)
      return
    }

    if (heatmapImage) {
      setShowHeatmap(true)
      return
    }

    setLoading(true)
    setLoadingText('Generating heatmap...')
    try {
      const res = await fetch(`${API_BASE}/heatmap`, { method: 'POST' })
      if (!res.ok) throw new Error('Heatmap generation failed')
      const data = await res.json()
      setHeatmapImage(data.heatmap_b64)
      setShowHeatmap(true)
    } catch (err) {
      showToast(err.message)
    } finally {
      setLoading(false)
    }
  }, [showHeatmap, heatmapImage, showToast])

  // ── Export actions ────────────────────────────────────────────
  const handleExport = useCallback(async (type) => {
    setLoading(true)
    setLoadingText(`Exporting ${type.toUpperCase()}...`)
    try {
      const res = await fetch(`${API_BASE}/export/${type}`, { method: 'POST' })
      if (!res.ok) throw new Error(`Export failed`)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const extensions = { png: 'png', pdf: 'pdf', csv: 'csv' }
      a.download = `ultrasound_report.${extensions[type]}`
      a.click()
      URL.revokeObjectURL(url)
      showToast(`${type.toUpperCase()} exported!`, 'success')
    } catch (err) {
      showToast(err.message)
    } finally {
      setLoading(false)
    }
  }, [showToast])

  // ── Splash Screen ─────────────────────────────────────────────
  if (!modelReady) {
    return (
      <div className="splash-screen">
        <div className="splash-logo">
          <img src="logo-full.png" alt="SonoClarity" style={{ width: 120, height: 120, objectFit: 'contain' }} />
        </div>
        <div className="splash-title">SonoClarity</div>
        <div className="splash-subtitle">Initializing AI model...</div>
        <div className="splash-progress">
          <div className="splash-progress-bar"></div>
        </div>
        <div className="splash-status">Loading Detectron2 + PointRend</div>
      </div>
    )
  }

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">
            <img src="logo-icon.png" alt="SonoClarity Icon" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
          <h1>SonoClarity</h1>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'intake' ? 'active' : ''}`}
          onClick={() => setActiveTab('intake')}
        >
          📋 Patient Intake
        </button>
        <button
          className={`tab-btn ${activeTab === 'results' ? 'active' : ''} ${!analysisResult ? 'disabled' : ''}`}
          onClick={() => analysisResult && setActiveTab('results')}
        >
          📊 Results{analysisResult ? ` (${analysisResult.numLesions} lesion${analysisResult.numLesions !== 1 ? 's' : ''})` : ''}
        </button>
        <button
          className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ Settings
        </button>
        <button
          className={`tab-btn ${activeTab === 'about' ? 'active' : ''}`}
          onClick={() => setActiveTab('about')}
        >
          ℹ️ About
        </button>
      </nav>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'intake' && (
          <PatientIntake onAnalyze={handleAnalyze} />
        )}

        {activeTab === 'results' && analysisResult && (
          <AnalysisResult
            result={analysisResult}
            showHeatmap={showHeatmap}
            heatmapImage={heatmapImage}
            heatmapEnabled={settings.showHeatmap}
            onToggleHeatmap={handleToggleHeatmap}
            onExport={handleExport}
            onBack={() => setActiveTab('intake')}
            settings={settings}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsPanel settings={settings} onChange={setSettings} />
        )}

        {activeTab === 'about' && (
          <AboutPanel />
        )}
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="spinner-overlay">
          <div className="spinner"></div>
          <p className="spinner-text">{loadingText}</p>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  )
}

export default App
