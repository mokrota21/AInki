import React, { useRef, useEffect, useState } from 'react'

const PDFViewer = ({ pdfUrl, currentPage, onPageChange, onTotalPagesChange }) => {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const [pdfDoc, setPdfDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scale, setScale] = useState(1)
  const renderTaskRef = useRef(null)
  const timeoutRef = useRef(null)
  const [isPanning, setIsPanning] = useState(false)
  const panStateRef = useRef({ x: 0, y: 0, left: 0, top: 0 })
  const isPanningRef = useRef(false)

  const clampScale = React.useCallback((value) => {
    return Math.min(3, Math.max(0.5, value))
  }, [])

  useEffect(() => {
    if (!pdfUrl) return

    const loadPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Configure PDF.js worker
        if (window.pdfjsLib) {
          window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
        }

        // Load the PDF document
        const loadingTask = window.pdfjsLib.getDocument(pdfUrl)
        const pdf = await loadingTask.promise
        setPdfDoc(pdf)
        
        // Notify parent of total pages
        if (onTotalPagesChange) {
          onTotalPagesChange(pdf.numPages)
        }
        
        setLoading(false)
      } catch (err) {
        console.error('Error loading PDF:', err)
        setError('Failed to load PDF document')
        setLoading(false)
      }
    }

    loadPDF()

    // Cleanup function
    return () => {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel()
        renderTaskRef.current = null
      }
    }
  }, [pdfUrl])

  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Debounce the render to prevent rapid successive renders
    timeoutRef.current = setTimeout(async () => {
      try {
        // Cancel any previous render task
        if (renderTaskRef.current) {
          renderTaskRef.current.cancel()
          renderTaskRef.current = null
        }

        const page = await pdfDoc.getPage(currentPage + 1) // PDF.js uses 1-based indexing
        const canvas = canvasRef.current
        const container = containerRef.current
        const context = canvas.getContext('2d')

        // Get container dimensions (account for padding)
        const containerWidth = container.clientWidth - 32 // 16px padding on each side
        const containerHeight = container.clientHeight - 32 // 16px padding on each side

        // Calculate scale to fit the container
        const viewport = page.getViewport({ scale: 1 })
        const scaleX = containerWidth / viewport.width
        const scaleY = containerHeight / viewport.height
        const fitScale = Math.min(scaleX, scaleY) * 0.9 // 90% to leave some padding
        const finalScale = fitScale * scale // Apply user zoom

        const scaledViewport = page.getViewport({ scale: finalScale })

        // Set canvas dimensions - this will clear the canvas
        canvas.width = scaledViewport.width
        canvas.height = scaledViewport.height

        // Ensure canvas doesn't exceed container when zoomed
        if (scaledViewport.width > containerWidth || scaledViewport.height > containerHeight) {
          // Canvas is larger than container, ensure it's positioned at top-left
          canvas.style.maxWidth = 'none'
          canvas.style.maxHeight = 'none'
        } else {
          // Canvas fits in container, center it
          canvas.style.maxWidth = '100%'
          canvas.style.maxHeight = '100%'
        }

        // Render the page
        const renderContext = {
          canvasContext: context,
          viewport: scaledViewport
        }

        // Store the render task so we can cancel it if needed
        const renderTask = page.render(renderContext)
        renderTaskRef.current = renderTask

        await renderTask.promise
        renderTaskRef.current = null
      } catch (err) {
        // Don't show error if it was cancelled
        if (err.name !== 'RenderingCancelledException') {
          console.error('Error rendering PDF page:', err)
          setError('Failed to render PDF page')
        }
        renderTaskRef.current = null
      }
    }, 100) // 100ms debounce

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel()
        renderTaskRef.current = null
      }
    }
  }, [pdfDoc, currentPage, scale])

  // Handle window resize to recalculate scale
  useEffect(() => {
    const handleResize = () => {
      // Trigger re-render when window resizes
      if (pdfDoc && canvasRef.current) {
        // Force re-render by nudging scale within clamp bounds
        setScale(prev => clampScale(prev + 0.001))
        setTimeout(() => setScale(prev => clampScale(prev - 0.001)), 10)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [pdfDoc, clampScale])

  useEffect(() => {
    isPanningRef.current = isPanning
  }, [isPanning])

  useEffect(() => {
    const handleWindowMouseUp = () => {
      if (isPanningRef.current) {
        setIsPanning(false)
      }
    }

    window.addEventListener('mouseup', handleWindowMouseUp)
    return () => {
      window.removeEventListener('mouseup', handleWindowMouseUp)
    }
  }, [])

  const beginPan = React.useCallback((clientX, clientY) => {
    const container = containerRef.current
    if (!container) return
    panStateRef.current = {
      x: clientX,
      y: clientY,
      left: container.scrollLeft,
      top: container.scrollTop
    }
    setIsPanning(true)
  }, [])

  const updatePan = React.useCallback((clientX, clientY) => {
    const container = containerRef.current
    if (!container) return
    const { x, y, left, top } = panStateRef.current
    container.scrollLeft = left - (clientX - x)
    container.scrollTop = top - (clientY - y)
  }, [])

  const endPan = React.useCallback(() => {
    if (isPanningRef.current) {
      setIsPanning(false)
    }
  }, [])

  const handleMouseDown = React.useCallback((event) => {
    if (event.button !== 0) return
    event.preventDefault()
    beginPan(event.clientX, event.clientY)
  }, [beginPan])

  const handleMouseMove = React.useCallback((event) => {
    if (!isPanningRef.current) return
    event.preventDefault()
    updatePan(event.clientX, event.clientY)
  }, [updatePan])

  const handleMouseUp = React.useCallback(() => {
    endPan()
  }, [endPan])

  const handleMouseLeave = React.useCallback(() => {
    endPan()
  }, [endPan])

  const handleWheel = React.useCallback((event) => {
    if (!event.ctrlKey && !event.metaKey) return
    event.preventDefault()
    setScale(prev => clampScale(event.deltaY < 0 ? prev * 1.1 : prev / 1.1))
  }, [clampScale])

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div className="spinner"></div>
        <div>Loading PDF...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        flexDirection: 'column',
        gap: '1rem',
        color: '#dc3545'
      }}>
        <div style={{ fontSize: '1.2rem' }}>⚠️ {error}</div>
        <div style={{ fontSize: '0.9rem', color: '#6c757d' }}>
          Make sure the PDF file is accessible
        </div>
      </div>
    )
  }

  const handleZoomIn = () => {
    setScale(prev => clampScale(prev * 1.2))
  }

  const handleZoomOut = () => {
    setScale(prev => clampScale(prev / 1.2))
  }

  const handleResetZoom = () => {
    setScale(1)
  }

  return (
    <div className="pdf-viewer">
      <div className="pdf-viewer__toolbar" role="group" aria-label="PDF zoom controls">
        <button type="button" onClick={handleZoomOut} title="Zoom out">
          −
        </button>
        <span className="pdf-viewer__scale">{Math.round(scale * 100)}%</span>
        <button type="button" onClick={handleZoomIn} title="Zoom in">
          +
        </button>
        <button type="button" onClick={handleResetZoom} title="Reset zoom">
          Reset
        </button>
      </div>
      <div
        ref={containerRef}
        className={`pdf-viewer__canvas-container${isPanning ? ' is-panning' : ''}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onWheel={handleWheel}
      >
        <div className="pdf-viewer__canvas-scroller">
          <canvas ref={canvasRef} className="pdf-viewer__canvas" />
        </div>
      </div>
    </div>
  )
}

export default PDFViewer
