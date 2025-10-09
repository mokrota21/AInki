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
        // Force re-render by updating scale slightly
        setScale(prev => prev + 0.001)
        setTimeout(() => setScale(prev => prev - 0.001), 10)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [pdfDoc])

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
    setScale(prev => Math.min(prev * 1.2, 3)) // Max 3x zoom
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev / 1.2, 0.5)) // Min 0.5x zoom
  }

  const handleResetZoom = () => {
    setScale(1)
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100%',
      padding: '1rem'
    }}>
      {/* Zoom Controls */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '0.5rem',
        marginBottom: '1rem',
        padding: '0.5rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px',
        border: '1px solid #dee2e6'
      }}>
        <button
          onClick={handleZoomOut}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.875rem',
            border: '1px solid #6c757d',
            borderRadius: '4px',
            backgroundColor: '#fff',
            cursor: 'pointer'
          }}
        >
          Zoom Out
        </button>
        <span style={{ fontSize: '0.875rem', color: '#6c757d', minWidth: '60px', textAlign: 'center' }}>
          {Math.round(scale * 100)}%
        </span>
        <button
          onClick={handleZoomIn}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.875rem',
            border: '1px solid #6c757d',
            borderRadius: '4px',
            backgroundColor: '#fff',
            cursor: 'pointer'
          }}
        >
          Zoom In
        </button>
        <button
          onClick={handleResetZoom}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.875rem',
            border: '1px solid #6c757d',
            borderRadius: '4px',
            backgroundColor: '#fff',
            cursor: 'pointer',
            marginLeft: '0.5rem'
          }}
        >
          Reset
        </button>
      </div>

      {/* PDF Canvas Container */}
      <div 
        ref={containerRef}
        style={{ 
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          border: '1px solid #dee2e6',
          padding: '1rem',
          position: 'relative'
        }}
      >
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          minHeight: '100%',
          minWidth: '100%'
        }}>
          <canvas
            ref={canvasRef}
            style={{
              border: '1px solid #ddd',
              borderRadius: '4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              backgroundColor: '#fff',
              display: 'block',
              flexShrink: 0
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default PDFViewer
