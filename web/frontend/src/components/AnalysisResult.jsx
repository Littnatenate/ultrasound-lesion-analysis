import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileImage, FileText, Table, CheckCircle2, ChevronUp, Flame } from 'lucide-react'
import ImageViewer from './ImageViewer'
import BorderBeam from './ui/BorderBeam'
export default function AnalysisResult({
    result,
    onExport,
    onBack,
    settings
}) {
    const { visImg, results, seeDoctor, age, site, timestamp } = result
    const [showExportMenu, setShowExportMenu] = useState(false)
    const [exportSuccess, setExportSuccess] = useState(null)

    const handleExport = (type) => {
        onExport(type)
        setExportSuccess(type)
        setShowExportMenu(false)
        setTimeout(() => setExportSuccess(null), 3000)
    }


    return (
        <div className="result-layout fade-in">
            {/* Left: Annotated Image */}
            <div className="card card-accent card-glass result-image-container">
                <ImageViewer
                    src={`data:image/jpeg;base64,${visImg}`}
                    alt="Analysis result"
                />
            </div>

            {/* Right: Stats Panel */}
            <div className="result-stats-panel overflow-y-auto min-h-0">
                {/* Back button */}
                <button className="btn btn-outline" style={{ width: '100%' }} onClick={onBack}>
                    ← Back to Intake
                </button>

                {/* Risk Badge */}
                <div className={`risk-badge ${seeDoctor ? 'risk-badge-danger' : 'risk-badge-safe'}`}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 500, opacity: 0.8, marginBottom: 4 }}>
                        See Doctor:
                    </div>
                    <div>{seeDoctor ? 'YES' : 'NO'}</div>
                </div>



                {/* Bento Grid: Clinical Statistics */}
                <div className="grid grid-cols-1 md:grid-cols-2 relative z-10 pt-4" style={{ gap: '16px' }}>
                    {/* Patient Info Card */}
                    <div className="card card-glass relative flex flex-col justify-start" style={{ padding: '16px' }}>
                        <h4 className="font-bold uppercase tracking-wider text-purple-300/80 mb-3" style={{ fontSize: '13px' }}>Patient Info</h4>
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-gray-400">Age</span>
                            <span className="text-md font-medium text-white">{age} yrs</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Site</span>
                            <span className="text-md font-medium text-white">{site}</span>
                        </div>
                    </div>

                    {/* Scan Time Card */}
                    <div className="card card-glass relative flex flex-col justify-start" style={{ padding: '16px' }}>
                        <h4 className="font-bold uppercase tracking-wider text-blue-300/80 mb-3" style={{ fontSize: '13px' }}>Scan Analyzed</h4>
                        <div className="text-md font-medium text-white">
                            {timestamp ? timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            {timestamp && timestamp.toLocaleDateString()}
                        </div>
                    </div>

                    {/* Lesion Details Card (Spans full width) */}
                    <div className="card card-glass relative flex flex-col justify-start overflow-hidden col-span-1 md:col-span-2" style={{ padding: '16px' }}>
                        <BorderBeam duration={10} size={400} className="opacity-40" />
                        <h4 className="font-bold uppercase tracking-wider text-accent/90 mb-4 relative z-10" style={{ fontSize: '13px' }}>Findings</h4>
                        <div className="relative z-10" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {results.length === 0 ? (
                                <p className="text-sm italic text-gray-400 text-center py-4">
                                    No lesions detected in this scan.
                                </p>
                            ) : (
                                results.map((r, i) => (
                                    <div key={i} className="bg-black/20 rounded-lg border border-white/5" style={{ padding: '12px' }}>
                                        <div className="flex justify-between items-center" style={{ marginBottom: '12px' }}>
                                            <span className="font-semibold text-purple-200" style={{ fontSize: '15px' }}>Lump #{i + 1}</span>
                                            <span className="text-xs rounded bg-white/10 text-white border border-white/10" style={{ padding: '4px 8px' }}>
                                                {r.circularity >= 0.8 ? 'Smooth' : r.circularity >= 0.6 ? 'Mod. irregular' : 'Irregular'}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-2" style={{ gap: '10px' }}>
                                            <div>
                                                <div className="text-gray-500" style={{ fontSize: '11px', marginBottom: '2px' }}>Height</div>
                                                <div className="font-medium text-white" style={{ fontSize: '14px' }}>{r.h_cm.toFixed(2)} cm</div>
                                            </div>
                                            <div>
                                                <div className="text-gray-500" style={{ fontSize: '11px', marginBottom: '2px' }}>Width</div>
                                                <div className="font-medium text-white" style={{ fontSize: '14px' }}>{r.w_cm.toFixed(2)} cm</div>
                                            </div>
                                            <div>
                                                <div className="text-gray-500" style={{ fontSize: '11px', marginBottom: '2px' }}>Max Area</div>
                                                <div className="font-medium text-white" style={{ fontSize: '14px' }}>{r.area_cm2.toFixed(2)} cm²</div>
                                            </div>
                                            <div>
                                                <div className="text-gray-500" style={{ fontSize: '11px', marginBottom: '2px' }}>Circularity</div>
                                                <div className="font-medium text-white" style={{ fontSize: '14px' }}>{r.circularity.toFixed(2)}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Export Buttons */}
                <div className="export-workflow mt-6 relative">
                    <AnimatePresence>
                        {showExportMenu && (
                            <>
                                {/* Overlay to obscure stats and focus on export */}
                                <motion.div 
                                    className="fixed inset-0 z-40 bg-[#0f111a]/60 backdrop-blur-[2px] rounded-r-2xl"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    onClick={() => setShowExportMenu(false)}
                                    style={{ margin: -24 }} // counteract parent padding
                                />
                                
                                {/* Expanded Action Menu */}
                                <motion.div 
                                    className="export-menu absolute bottom-full left-0 right-0 bg-[#1e212d]/95 border border-purple-500/30 shadow-[0_10px_40px_rgba(0,0,0,0.5)] z-50 backdrop-blur-xl flex flex-col"
                                    style={{ padding: '16px', borderRadius: '16px', gap: '8px', marginBottom: '16px' }}
                                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 20, scale: 0.95 }}
                                    transition={{ type: 'spring', stiffness: 350, damping: 25 }}
                                >
                                    <div className="font-bold uppercase tracking-wider text-gray-400" style={{ fontSize: '11px', padding: '0 8px', marginBottom: '8px' }}>Select Format</div>
                                    <button className="flex items-center w-full transition-colors text-left group hover:bg-white/5" style={{ padding: '12px', borderRadius: '12px', gap: '16px' }} onClick={() => handleExport('pdf')}>
                                        <div className="bg-blue-500/10 transition-colors group-hover:bg-blue-500/20" style={{ padding: '12px', borderRadius: '8px' }}>
                                            <FileText size={22} className="text-blue-400" />
                                        </div>
                                        <div>
                                            <div className="text-base font-semibold text-gray-100">Professional Report (PDF)</div>
                                            <div className="text-xs text-gray-400" style={{ marginTop: '4px' }}>Images, measurements & assessment</div>
                                        </div>
                                    </button>
                                    <button className="flex items-center w-full transition-colors text-left group hover:bg-white/5" style={{ padding: '12px', borderRadius: '12px', gap: '16px' }} onClick={() => handleExport('png')}>
                                        <div className="bg-purple-500/10 transition-colors group-hover:bg-purple-500/20" style={{ padding: '12px', borderRadius: '8px' }}>
                                            <FileImage size={22} className="text-purple-400" />
                                        </div>
                                        <div>
                                            <div className="text-base font-semibold text-gray-100">Annotated Scan (PNG)</div>
                                            <div className="text-xs text-gray-400" style={{ marginTop: '4px' }}>Standalone high-res segmented image</div>
                                        </div>
                                    </button>
                                    <button className="flex items-center w-full transition-colors text-left group hover:bg-white/5" style={{ padding: '12px', borderRadius: '12px', gap: '16px' }} onClick={() => handleExport('csv')}>
                                        <div className="bg-emerald-500/10 transition-colors group-hover:bg-emerald-500/20" style={{ padding: '12px', borderRadius: '8px' }}>
                                            <Table size={22} className="text-emerald-400" />
                                        </div>
                                        <div>
                                            <div className="text-base font-semibold text-gray-100">Raw Metrics (CSV)</div>
                                            <div className="text-xs text-gray-400" style={{ marginTop: '4px' }}>Data table for longitudinal tracking</div>
                                        </div>
                                    </button>

                                </motion.div>
                            </>
                        )}
                    </AnimatePresence>

                    <button 
                        className={`w-full py-4 px-6 rounded-xl flex items-center justify-between gap-2 font-semibold transition-all duration-300 ${seeDoctor ? 'bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-200 border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]'}`}
                        onClick={() => setShowExportMenu(!showExportMenu)}
                    >
                        {exportSuccess ? (
                            <motion.div 
                                className="flex items-center justify-center gap-2 text-green-400 w-full"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                            >
                                <CheckCircle2 size={20} /> {exportSuccess.toUpperCase()} Saved Structure
                            </motion.div>
                        ) : (
                            <>
                                <span className="flex-1 text-center ml-6">Finalize & Export</span>
                                <motion.div animate={{ rotate: showExportMenu ? 180 : 0 }}>
                                    <ChevronUp size={20} className="opacity-70" />
                                </motion.div>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
