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
                <div className="app-logo-icon" style={{ width: 80, height: 80, margin: '0 auto 16px', background: 'transparent', boxShadow: 'none' }}>
                    <img src="logo-icon.png" alt="SonoClarity" style={{ width: '100%', height: '100%', objectFit: 'contain', mixBlendMode: 'screen' }} />
                </div>
                <h2>SonoClarity</h2>
                <p>Empowering Patients with Instant Clarity</p>
            </div>

            <div className="card card-accent card-glass" style={{ marginBottom: 16 }}>
                <div className="card-body">
                    <h3 style={{ marginBottom: 12 }}>Our Mission</h3>
                    <p style={{ fontSize: '0.9rem', lineHeight: 1.7, marginBottom: 16 }}>
                        Waiting for medical results can be one of the most stressful experiences a person can endure. At <strong>SonoClarity</strong>, our mission is to dramatically reduce the crushing anxiety and painful waiting times associated with breast cancer screenings.
                    </p>
                    <p style={{ fontSize: '0.9rem', lineHeight: 1.7 }}>
                        By leveraging state-of-the-art Artificial Intelligence, we aim to provide patients with instantaneous, easy-to-understand insights about their ultrasound scans. Whether you are tracking progressive changes during annual checkups or seeking immediate second-reader confidence, this tool is designed to save you time and bring you peace of mind.
                    </p>
                </div>
            </div>

            <div className="card card-glass" style={{ marginBottom: 16 }}>
                <div className="card-body">
                    <h3 style={{ marginBottom: 12 }}>Download Desktop App</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
                        Want to run our advanced AI models directly on your hospital computer with built-in patient registry tracking? Download our native Windows software.
                    </p>
                    <button className="btn btn-primary" style={{ width: '100%', padding: '12px' }} onClick={() => alert("The Desktop executable (.exe) is still compiling. Please check our GitHub repository for the latest release!")}>
                        <span style={{ marginRight: 8 }}>⬇️</span> Download SonoClarity (.exe)
                    </button>
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
