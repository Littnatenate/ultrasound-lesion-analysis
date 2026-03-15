import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ClipboardList, Activity, Settings, Info, Laptop, Server } from 'lucide-react'
import PatientIntake from './components/PatientIntake'
import AnalysisResult from './components/AnalysisResult'
import SettingsPanel from './components/SettingsPanel'
import AboutPanel from './components/AboutPanel'
import SplashScreen from './components/SplashScreen'
import AnimatedBeam from './components/ui/AnimatedBeam'
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

  // Settings
  const [settings, setSettings] = useState({
    theme: 'dark', // 'light' or 'dark'
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

  // ── Render ─────────────────────────────────────────────────────

  return (
    <>
    {/* Splash Screen with cross-fade exit */}
    <SplashScreen isVisible={!modelReady} />

    {/* Main App with entrance animation */}
    <AnimatePresence>
    {modelReady && (
    <motion.div
      className={`app-layout ${settings.theme === 'light' ? 'light-theme' : ''}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.3 }}
    >
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon" style={{ background: 'transparent', boxShadow: 'none', width: 160, height: 60, marginLeft: -16, marginRight: -55, marginTop: -15 }}>
            <img src="sc-icon-transparent.png" alt="SonoClarity Icon" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </div>
          <h1 style={{ fontSize: '2rem', marginLeft: 0 }}>SonoClarity</h1>
        </div>
      </header>

      {/* Tab Navigation — Floating Tabs with Sliding Highlight */}
      <nav className="tab-nav">
        {[
          { id: 'intake', label: 'Patient Intake', icon: ClipboardList },
          { id: 'results', label: `Results${analysisResult ? ` (${analysisResult.numLesions})` : ''}`, icon: Activity, disabled: !analysisResult },
          { id: 'settings', label: 'Settings', icon: Settings },
          { id: 'about', label: 'About', icon: Info },
        ].map(({ id, label, icon: Icon, disabled }) => (
          <button
            key={id}
            className={`tab-btn ${activeTab === id ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            onClick={() => !disabled && setActiveTab(id)}
            style={{ position: 'relative' }}
          >
            {activeTab === id && (
              <motion.div
                className="tab-highlight"
                layoutId="activeTab"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <span style={{ position: 'relative', zIndex: 1, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Icon size={16} />
              {label}
            </span>
          </button>
        ))}
      </nav>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'intake' && (
          <PatientIntake onAnalyze={handleAnalyze} />
        )}

        {activeTab === 'results' && analysisResult && (
          <AnalysisResult
            result={analysisResult}
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

      {/* Loading Overlay - Animated Beam Pipeline */}
      <AnimatePresence>
        {loading && (
          <motion.div 
            className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background/80 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="relative flex w-full max-w-[500px] items-center justify-between px-10 py-10">
              {/* The Beam */}
              <AnimatedBeam 
                pathData="M 40 50 Q 250 150 460 50"
                className="z-0"
              />
              
              {/* Left Node: Client */}
              <motion.div 
                className="z-10 flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-white/10 bg-black/40 shadow-[0_0_20px_rgba(123,94,167,0.3)] backdrop-blur-lg"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                <Laptop className="text-purple-300" size={28} />
              </motion.div>

              {/* Right Node: Server/AI */}
              <motion.div 
                className="z-10 flex h-20 w-20 items-center justify-center rounded-2xl border-2 border-white/10 bg-black/40 shadow-[0_0_30px_rgba(168,85,247,0.4)] backdrop-blur-lg"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                <Server className="text-fuchsia-400" size={32} />
              </motion.div>
            </div>
            
            <motion.p 
              className="mt-8 text-lg font-medium tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-fuchsia-300"
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              {loadingText}
            </motion.p>
            <motion.p 
              className="mt-2 text-sm text-gray-400"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Processing via secured pipeline...
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </motion.div>
    )}
    </AnimatePresence>
    </>
  )
}

export default App
