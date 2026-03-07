export default function SettingsPanel({ settings, onChange }) {
    const toggle = (key) => {
        onChange({ ...settings, [key]: !settings[key] })
    }

    const toggleItems = [
        { key: 'showHeatmap', label: 'Heatmap Overlay', description: 'Show the heatmap toggle button on the results page' },
        { key: 'showPng', label: 'PNG Export', description: 'Show the Save PNG button' },
        { key: 'showPdf', label: 'PDF Report', description: 'Show the Save PDF button' },
        { key: 'showCsv', label: 'CSV Log', description: 'Show the Save CSV button' },
    ]

    return (
        <div style={{ maxWidth: 600 }} className="fade-in">
            <div className="card card-accent card-glass">
                <div className="card-body">
                    <h2 style={{ marginBottom: 4 }}>Settings</h2>
                    <p style={{ fontSize: '0.8rem', marginBottom: 24 }}>
                        Configure which features are visible on the results page.
                    </p>

                    {toggleItems.map(({ key, label, description }) => (
                        <div className="toggle-row" key={key}>
                            <div>
                                <div className="toggle-label">{label}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                    {description}
                                </div>
                            </div>
                            <label className="toggle-switch">
                                <input
                                    type="checkbox"
                                    checked={settings[key]}
                                    onChange={() => toggle(key)}
                                />
                                <span className="toggle-slider"></span>
                            </label>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
