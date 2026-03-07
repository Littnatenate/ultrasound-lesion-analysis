import { useState, useRef } from 'react'

export default function ImageViewer({ src, alt }) {
    const [isOpen, setIsOpen] = useState(false)
    const [scale, setScale] = useState(1)
    const [position, setPosition] = useState({ x: 0, y: 0 })
    const [dragging, setDragging] = useState(false)
    const dragStart = useRef({ x: 0, y: 0 })
    const posStart = useRef({ x: 0, y: 0 })

    const handleOpen = () => {
        setIsOpen(true)
        setScale(1)
        setPosition({ x: 0, y: 0 })
    }

    const handleWheel = (e) => {
        e.preventDefault()
        e.stopPropagation()
        const delta = e.deltaY > 0 ? -0.2 : 0.2
        setScale(prev => {
            const next = Math.max(0.5, Math.min(5, prev + delta))
            // Reset position when zooming out to 1x
            if (next <= 1) setPosition({ x: 0, y: 0 })
            return next
        })
    }

    const handleMouseDown = (e) => {
        if (scale <= 1) return
        e.preventDefault()
        setDragging(true)
        dragStart.current = { x: e.clientX, y: e.clientY }
        posStart.current = { ...position }
    }

    const handleMouseMove = (e) => {
        if (!dragging) return
        const dx = e.clientX - dragStart.current.x
        const dy = e.clientY - dragStart.current.y
        setPosition({
            x: posStart.current.x + dx,
            y: posStart.current.y + dy,
        })
    }

    const handleMouseUp = () => {
        setDragging(false)
    }

    const handleReset = (e) => {
        e.stopPropagation()
        setScale(1)
        setPosition({ x: 0, y: 0 })
    }

    return (
        <>
            <img
                src={src}
                alt={alt}
                onClick={handleOpen}
                style={{ cursor: 'zoom-in' }}
            />

            {isOpen && (
                <div
                    className="lightbox-overlay"
                    onClick={() => setIsOpen(false)}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                >
                    <div className="lightbox-controls">
                        <button className="lightbox-btn" onClick={(e) => { e.stopPropagation(); setScale(s => Math.min(5, s + 0.5)) }}>
                            🔍+
                        </button>
                        <button className="lightbox-btn" onClick={handleReset}>
                            1:1
                        </button>
                        <button className="lightbox-btn" onClick={(e) => { e.stopPropagation(); setScale(s => { const n = Math.max(0.5, s - 0.5); if (n <= 1) setPosition({ x: 0, y: 0 }); return n; }) }}>
                            🔍−
                        </button>
                        <button className="lightbox-btn lightbox-close" onClick={() => setIsOpen(false)}>
                            ✕
                        </button>
                    </div>
                    <div className="lightbox-hint">
                        {scale > 1 ? 'Click and drag to pan • Scroll to zoom' : 'Scroll to zoom • Click outside to close'}
                    </div>
                    <div
                        className="lightbox-content"
                        onClick={(e) => e.stopPropagation()}
                        onWheel={handleWheel}
                        onMouseDown={handleMouseDown}
                        style={{ cursor: scale > 1 ? (dragging ? 'grabbing' : 'grab') : 'default' }}
                    >
                        <img
                            src={src}
                            alt={alt}
                            draggable={false}
                            style={{
                                transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                                transition: dragging ? 'none' : 'transform 0.2s ease',
                            }}
                        />
                    </div>
                </div>
            )}
        </>
    )
}
