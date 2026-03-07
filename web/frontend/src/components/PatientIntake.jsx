import { useState, useRef, useCallback } from 'react'

export default function PatientIntake({ onAnalyze }) {
    const [age, setAge] = useState('')
    const [site, setSite] = useState('Breast')
    const [imageFile, setImageFile] = useState(null)
    const [preview, setPreview] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const fileInput = useRef(null)

    const handleFile = useCallback((file) => {
        if (!file) return
        if (!file.type.startsWith('image/')) return
        setImageFile(file)
        const reader = new FileReader()
        reader.onload = (e) => setPreview(e.target.result)
        reader.readAsDataURL(file)
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        handleFile(file)
    }, [handleFile])

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!imageFile || !age) return
        onAnalyze(imageFile, parseInt(age), site)
    }

    const isValid = imageFile && age && parseInt(age) > 0

    return (
        <div className="intake-layout fade-in">
            {/* Left: Form */}
            <div className="card card-accent card-glass">
                <div className="card-body">
                    <h2 style={{ marginBottom: 4 }}>Patient Analysis</h2>
                    <p style={{ fontSize: '0.8rem', marginBottom: 24 }}>
                        Fill in clinical details and select an ultrasound scan to begin.
                    </p>

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label className="form-label">Patient Age</label>
                            <input
                                className="form-input"
                                type="number"
                                min="1"
                                max="120"
                                placeholder="Enter age..."
                                value={age}
                                onChange={(e) => setAge(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Exam Site</label>
                            <select className="form-select" value={site} onChange={(e) => setSite(e.target.value)}>
                                <option>Breast</option>
                                <option>Axilla</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Ultrasound Image</label>
                            <div
                                className={`dropzone ${dragOver ? 'drag-over' : ''}`}
                                onClick={() => fileInput.current?.click()}
                                onDrop={handleDrop}
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                                onDragLeave={() => setDragOver(false)}
                            >
                                {imageFile ? (
                                    <>
                                        <p className="dropzone-icon">✅</p>
                                        <p className="dropzone-text">{imageFile.name}</p>
                                        <p className="dropzone-hint">Click to change</p>
                                    </>
                                ) : (
                                    <>
                                        <p className="dropzone-icon">📁</p>
                                        <p className="dropzone-text">Drop ultrasound image here</p>
                                        <p className="dropzone-hint">or click to browse • JPG, PNG, BMP</p>
                                    </>
                                )}
                            </div>
                            <input
                                ref={fileInput}
                                type="file"
                                accept="image/*"
                                style={{ display: 'none' }}
                                onChange={(e) => handleFile(e.target.files[0])}
                            />
                        </div>

                        <button type="submit" className="btn btn-primary" disabled={!isValid} style={{ width: '100%', padding: '14px' }}>
                            🔬 Run Analysis
                        </button>
                    </form>
                </div>
            </div>

            {/* Right: Image Preview */}
            <div className="card card-glass preview-container">
                {preview ? (
                    <img src={preview} alt="Ultrasound preview" />
                ) : (
                    <div className="preview-placeholder">
                        <p className="preview-placeholder-icon">🖼️</p>
                        <p>Image preview will appear here</p>
                    </div>
                )}
            </div>
        </div>
    )
}
