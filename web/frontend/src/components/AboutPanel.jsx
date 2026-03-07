export default function AboutPanel() {
    const techStack = [
        { icon: '🧠', name: 'Detectron2' },
        { icon: '🔥', name: 'PyTorch' },
        { icon: '⚡', name: 'FastAPI' },
        { icon: '⚛️', name: 'React' },
        { icon: '🎨', name: 'Vite' },
        { icon: '🖼️', name: 'OpenCV' },
        { icon: '🪟', name: 'pywebview' },
        { icon: '📄', name: 'fpdf2' },
    ]

    return (
        <div className="about-layout fade-in">
            <div className="about-header">
                <div className="app-logo-icon" style={{ width: 64, height: 64, fontSize: 32, margin: '0 auto 16px', borderRadius: 16 }}>
                    🔬
                </div>
                <h2>Ultrasound Lesion Analysis</h2>
                <p>AI-powered clinical decision support for ultrasound diagnostics</p>
            </div>

            <div className="card card-accent card-glass" style={{ marginBottom: 16 }}>
                <div className="card-body">
                    <h3 style={{ marginBottom: 12 }}>About This Project</h3>
                    <p style={{ fontSize: '0.85rem', lineHeight: 1.7 }}>
                        This application uses a Detectron2 instance segmentation model with PointRend
                        refinement to detect and analyze breast lesions in ultrasound images. The model
                        was trained on annotated clinical ultrasound data and provides automated
                        measurements, boundary analysis, and risk assessment to support clinical
                        decision-making.
                    </p>
                </div>
            </div>

            <div className="card card-glass" style={{ marginBottom: 16 }}>
                <div className="card-body">
                    <h3 style={{ marginBottom: 4 }}>Key Features</h3>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <div className="stat-row">
                            <span className="stat-label">🎯 Detection</span>
                            <span className="stat-value">Instance segmentation with PointRend</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">📏 Measurements</span>
                            <span className="stat-value">Height, width, area, circularity</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">⚠️ Risk Model</span>
                            <span className="stat-value">Logistic regression (see doctor probability)</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">🔥 Heatmap</span>
                            <span className="stat-value">Radial gradient risk overlay</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">📄 Reports</span>
                            <span className="stat-value">PDF, PNG, CSV export</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card card-glass">
                <div className="card-body">
                    <h3 style={{ marginBottom: 4 }}>Tech Stack</h3>
                    <div className="tech-grid">
                        {techStack.map(({ icon, name }) => (
                            <div className="tech-item" key={name}>
                                <div className="tech-item-icon">{icon}</div>
                                {name}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
