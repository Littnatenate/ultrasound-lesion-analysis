export default function SettingsPanel({ settings, onChange }) {
    const toggle = (key) => {
        onChange({ ...settings, [key]: !settings[key] })
    }

    return (
        <div style={{ maxWidth: 600 }} className="fade-in">
            <div className="card card-accent card-glass">
                <div className="card-body">
                    <h2 style={{ marginBottom: 4 }}>Settings</h2>
                    <p style={{ fontSize: '0.8rem', marginBottom: 24 }}>
                        Configure the visual overlays on the results page.
                    </p>

                    <div className="toggle-row">
                        <div>
                            <div className="toggle-label">
                                Heatmap Overlay
                                <span title="Overlays a color-coded thermal map highlighting the specific regions the AI focused on to make its risk prediction." style={{ marginLeft: '6px', cursor: 'help', color: 'var(--primary)', borderBottom: '1px dotted var(--primary)' }}>
                                    (?)
                                </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                Show the heatmap toggle button on the results page
                            </div>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={settings.showHeatmap}
                                onChange={() => toggle('showHeatmap')}
                            />
                            <span className="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    )
}
