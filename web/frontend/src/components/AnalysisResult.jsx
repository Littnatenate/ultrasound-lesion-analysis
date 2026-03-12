import ImageViewer from './ImageViewer'

export default function AnalysisResult({
    result,
    showHeatmap,
    heatmapImage,
    heatmapEnabled,
    onToggleHeatmap,
    onExport,
    onBack,
    settings
}) {
    const { visImg, results, seeDoctor, age, site, timestamp } = result

    const displayImage = showHeatmap && heatmapImage ? heatmapImage : visImg

    return (
        <div className="result-layout fade-in">
            {/* Left: Annotated Image */}
            <div className="card card-accent card-glass result-image-container">
                <ImageViewer
                    src={`data:image/jpeg;base64,${displayImage}`}
                    alt="Analysis result"
                />
            </div>

            {/* Right: Stats Panel */}
            <div className="result-stats-panel">
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



                {/* Clinical Statistics */}
                <div className="card card-glass">
                    <div className="card-body">
                        <h3 style={{ marginBottom: 12 }}>Clinical Statistics</h3>

                        <div className="stat-row">
                            <span className="stat-label">Patient Age</span>
                            <span className="stat-value">{age} years</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Exam Site</span>
                            <span className="stat-value">{site}</span>
                        </div>
                        {timestamp && (
                            <div className="stat-row">
                                <span className="stat-label">Analyzed</span>
                                <span className="stat-value">{timestamp.toLocaleTimeString()}</span>
                            </div>
                        )}

                        <div className="divider" style={{ margin: '12px 0' }} />

                        {results.length === 0 ? (
                            <p style={{ fontSize: '0.85rem', fontStyle: 'italic' }}>
                                No lesions detected.
                            </p>
                        ) : (
                            results.map((r, i) => (
                                <div key={i}>
                                    <div className="lump-header">Lump #{i + 1}</div>
                                    <div className="stat-row">
                                        <span className="stat-label">Dimensions</span>
                                        <span className="stat-value">{r.h_cm.toFixed(2)} × {r.w_cm.toFixed(2)} cm</span>
                                    </div>
                                    <div className="stat-row">
                                        <span className="stat-label">Max Area</span>
                                        <span className="stat-value">{r.area_cm2.toFixed(2)} cm²</span>
                                    </div>
                                    <div className="stat-row">
                                        <span className="stat-label">Boundary</span>
                                        <span className="stat-value">
                                            {r.circularity >= 0.8 ? 'Smooth' : r.circularity >= 0.6 ? 'Mod. irregular' : 'Irregular'} ({r.circularity.toFixed(2)})
                                        </span>
                                    </div>

                                    {i < results.length - 1 && <div className="divider" />}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Export Buttons */}
                <div className="export-bar">
                    <button className="btn btn-success" onClick={() => onExport('png')} title="Download a standalone image of the ultrasound scan with the AI bounding boxes.">
                        📸 Save PNG
                    </button>
                    <button className="btn btn-primary" onClick={() => onExport('pdf')} title="Generate a professional multi-page clinical report containing the image, measurements, and risk assessment.">
                        📄 Save PDF
                    </button>
                    <button className="btn btn-outline" onClick={() => onExport('csv')} title="Download a spreadsheet containing the raw numerical measurements for tracking analysis over time.">
                        📊 Save CSV
                    </button>
                    {heatmapEnabled && (
                        <button className="btn btn-warm" onClick={onToggleHeatmap} title="Toggle a color-coded thermal map highlighting the specific regions the AI focused on.">
                            🔥 {showHeatmap ? 'Hide' : 'Show'} Heatmap
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
