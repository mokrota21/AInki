import React from 'react'
import { useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { fetchFileContent, trackPage } from '../services/api'
import Dashboard from './Dashboard'

function Document() {
  const { id } = useParams()
  const [loading, setLoading] = React.useState(true)
  const [name, setName] = React.useState('')
  const [pdfUrl, setPdfUrl] = React.useState('')
  const [chunkCount, setChunkCount] = React.useState(0)
  const [currentPage, setCurrentPage] = React.useState(1)
  const [totalPages, setTotalPages] = React.useState(1)
  const [drawerOpen, setDrawerOpen] = React.useState(false)
  const [pageChunkRanges, setPageChunkRanges] = React.useState([])
  const pdfRef = React.useRef(null)

  React.useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await fetchFileContent(id)
        const docName = data?.name || 'Document'
        const chunks = Array.isArray(data?.chunks) ? data.chunks : []
        
        setName(docName)
        setChunkCount(chunks.length)
        
        // Create PDF URL - assuming the original file is in uploads with the same name
        const pdfFileName = docName.includes('.pdf') ? docName : `${docName}.pdf`
        const pdfUrl = `http://localhost:8000/uploads/${pdfFileName}`
        setPdfUrl(pdfUrl)
        
        // Estimate total pages based on chunks (rough approximation)
        setTotalPages(Math.max(1, Math.ceil(chunks.length / 3)))
        
        // Create page chunk ranges for tracking
        const ranges = []
        const chunksPerPage = Math.max(1, Math.ceil(chunks.length / Math.max(1, Math.ceil(chunks.length / 3))))
        for (let i = 0; i < Math.ceil(chunks.length / chunksPerPage); i++) {
          const startChunk = i * chunksPerPage
          const endChunk = Math.min((i + 1) * chunksPerPage - 1, chunks.length - 1)
          ranges.push({ startChunk, endChunk })
        }
        setPageChunkRanges(ranges)
        
      } catch (error) {
        toast.error('Failed to load document: ' + (error.response?.data?.detail || error.message))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Reset page when document changes
  React.useEffect(() => {
    setCurrentPage(1)
  }, [id])

  const sendTrackForCurrentPage = async () => {
    try {
      const range = pageChunkRanges[currentPage - 1] // Convert to 0-based index
      if (!range) return
      await trackPage({ docId: Number(id), chunkEnd: range.endChunk })
    } catch (e) {
      console.error('Tracking failed', e)
    }
  }

  const handlePrev = async () => {
    const prev = Math.max(1, currentPage - 1)
    if (prev !== currentPage) {
      // Track the page we're leaving (current page)
      await sendTrackForCurrentPage()
      setCurrentPage(prev)
    }
  }

  const handleNext = async () => {
    const next = Math.min(totalPages, currentPage + 1)
    if (next !== currentPage) {
      // Track the page we're leaving (current page)
      await sendTrackForCurrentPage()
      setCurrentPage(next)
    }
  }

  // Track when user leaves the page or navigates back/away
  React.useEffect(() => {
    const handleBeforeUnload = () => {
      const range = pageChunkRanges[currentPage - 1] // Convert to 0-based index
      if (!range) return
      // Fire-and-forget; navigator.sendBeacon preferable but our API requires auth header
      trackPage({ docId: Number(id), chunkEnd: range.endChunk }).catch(() => {})
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [id, currentPage, pageChunkRanges])


  return (
    <div style={{ position: 'fixed', inset: 0, background: '#f8f9fa' }}>
      {/* Menu button */}
      <button
        className="btn btn-secondary"
        onClick={() => setDrawerOpen(true)}
        style={{ position: 'fixed', top: '1rem', left: '1rem', zIndex: 1001 }}
      >
        Menu
      </button>

      {/* Document name */}
      <div style={{ position: 'fixed', top: '1.2rem', left: '5.5rem', right: '1rem', color: '#6c757d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {name}
      </div>

      {/* PDF Viewer */}
      <div style={{ position: 'absolute', top: '4rem', left: 0, right: 0, bottom: '80px', padding: '0 1rem' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <div className="spinner"></div>
          </div>
        ) : pdfUrl ? (
          <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <iframe
              ref={pdfRef}
              src={`${pdfUrl}#page=${currentPage}`}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}
              title={`PDF Viewer - ${name}`}
            />
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#6c757d' }}>
            <p>PDF not found</p>
          </div>
        )}
      </div>

      {/* Bottom controls */}
      <div style={{ position: 'fixed', left: 0, right: 0, bottom: 0, padding: '1rem', background: '#fff', borderTop: '1px solid #eee' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '800px', margin: '0 auto' }}>
          <button 
            className="btn btn-secondary" 
            onClick={handlePrev} 
            disabled={currentPage === 1}
            style={{ minWidth: '80px' }}
          >
            Previous
          </button>
          <span style={{ color: '#6c757d', fontSize: '0.9rem' }}>
            Page {currentPage} of {totalPages}
            {pageChunkRanges[currentPage - 1] ? ` · chunks ${pageChunkRanges[currentPage - 1].startChunk}–${pageChunkRanges[currentPage - 1].endChunk}` : ''}
          </span>
          <button 
            className="btn btn-primary" 
            onClick={handleNext} 
            disabled={currentPage >= totalPages}
            style={{ minWidth: '80px' }}
          >
            Next
          </button>
        </div>
      </div>

      {/* Overlay */}
      {drawerOpen && (
        <div
          onClick={() => setDrawerOpen(false)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000,
          }}
        />
      )}

      {/* Drawer */}
      <div
        style={{
          position: 'fixed', top: 0, left: 0, height: '100%', width: '420px', maxWidth: '90vw', background: '#fff',
          boxShadow: '0 0 20px rgba(0,0,0,0.2)', transform: drawerOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 250ms ease', zIndex: 1002, display: 'flex', flexDirection: 'column'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', borderBottom: '1px solid #eee' }}>
          <strong>Dashboard</strong>
          <button className="btn btn-secondary" onClick={() => setDrawerOpen(false)}>Close</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <Dashboard />
        </div>
      </div>
    </div>
  )
}

export default Document


