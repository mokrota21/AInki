import React from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import toast from 'react-hot-toast'
import { fetchFileContent, trackPage } from '../services/api'
import PDFViewer from './PDFViewer'
import 'katex/dist/katex.min.css'
import Dashboard from './Dashboard'

function Document() {
  const SENTINEL = '\u2063'
  const { id } = useParams()
  const [loading, setLoading] = React.useState(true)
  const [name, setName] = React.useState('')
  const [markdown, setMarkdown] = React.useState('')
  const viewerRef = React.useRef(null)
  const measureRef = React.useRef(null)
  const [pagesHtml, setPagesHtml] = React.useState([])
  const [pageStartAbs, setPageStartAbs] = React.useState([])
  const [pageEndAbs, setPageEndAbs] = React.useState([])
  const [pageChunkRanges, setPageChunkRanges] = React.useState([])
  const [chunkCount, setChunkCount] = React.useState(0)
  const [chunkBoundaries, setChunkBoundaries] = React.useState([])
  const [viewerHeight, setViewerHeight] = React.useState(0)
  const [currentPage, setCurrentPage] = React.useState(0)
  const [totalPages, setTotalPages] = React.useState(1)
  const [drawerOpen, setDrawerOpen] = React.useState(false)
  const controlsRef = React.useRef(null)
  const [controlsHeight, setControlsHeight] = React.useState(0)
  const [viewMode, setViewMode] = React.useState('markdown') // 'markdown' or 'pdf'
  const [pdfCurrentPage, setPdfCurrentPage] = React.useState(0)
  const [pdfTotalPages, setPdfTotalPages] = React.useState(1)
  const [pdfUrl, setPdfUrl] = React.useState('')
  const [mdPageInput, setMdPageInput] = React.useState('')
  const [pdfPageInput, setPdfPageInput] = React.useState('')
  // Track only on explicit page change via buttons

  React.useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await fetchFileContent(id)
        const docName = data?.name || 'Document'
        const folder = data?.folder || ''
        const chunks = Array.isArray(data?.chunks) ? data.chunks : []
        
        // Set PDF URL - assuming the original PDF is stored in uploads folder
        // docName already includes the .pdf extension, so use it directly
        const pdfUrl = `/api/uploads/${docName}` // This should match your backend upload path
        setPdfUrl(pdfUrl)
        const resolvedChunks = chunks.map((c) => {
          const raw = typeof c?.content === 'string' ? c.content : ''
          return raw.replace(/!\[[^\]]*\]\(([^)]+)\)/g, (match, p1) => {
          if (/^https?:\/\//i.test(p1)) return match
          const base = folder ? `${folder.replace(/\\/g, '/')}/${docName}.md` : `${docName}.md`
          const baseDir = base.substring(0, base.lastIndexOf('/'))
          const joined = baseDir ? `${baseDir}/${p1}` : p1
          return match.replace(p1, joined)
        })
        })

        const resolvedMd = resolvedChunks.join('')
        
        // Store chunk boundaries for proper pagination
        const chunkBoundaries = []
        let currentPos = 0
        for (let i = 0; i < resolvedChunks.length; i++) {
          chunkBoundaries.push(currentPos)
          currentPos += resolvedChunks[i].length
        }

        setName(docName)
        setChunkCount(resolvedChunks.length)
        setMarkdown(resolvedMd)
        setChunkBoundaries(chunkBoundaries)
      } catch (error) {
        toast.error('Failed to load document: ' + (error.response?.data?.detail || error.message))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Compute viewer height based on actual element sizing
  React.useEffect(() => {
    const compute = () => {
      const el = viewerRef.current
      if (!el) return
      const h = Math.max(100, el.clientHeight)
      setViewerHeight(h)
    }
    compute()
    window.addEventListener('resize', compute)
    return () => window.removeEventListener('resize', compute)
  }, [])

  // Build paginated HTML by measuring an offscreen rendered markdown
  React.useLayoutEffect(() => {
    const viewer = viewerRef.current
    const meas = measureRef.current
    if (!viewer || !meas) return
    if (!markdown || loading) return

    // Ensure measurement width matches viewer content width (account for paddings)
    const vStyle = getComputedStyle(viewer)
    const padL = parseFloat(vStyle.paddingLeft || '0') || 0
    const padR = parseFloat(vStyle.paddingRight || '0') || 0
    const contentWidth = Math.max(0, viewer.clientWidth - padL - padR)
    meas.style.width = `${contentWidth}px`

    // Helper to split a block element across pages at word boundaries using Range
    const splitBlockByHeight = (blockEl, firstPageAvailable, pageHeight) => {
      const results = []

      // Gather all text nodes for mapping index -> node/offset
      const walker = document.createTreeWalker(blockEl, NodeFilter.SHOW_TEXT, null)
      const textNodes = []
      let totalLength = 0
      while (walker.nextNode()) {
        const node = walker.currentNode
        const len = node.nodeValue ? node.nodeValue.length : 0
        textNodes.push({ node, start: totalLength, end: totalLength + len })
        totalLength += len
      }

      // If no text (e.g., images/math-only), do not split; return as a single chunk
      if (totalLength === 0) {
        return [{ html: blockEl.outerHTML, len: 0 }]
      }

      // Utility: map a character index to a specific text node and offset
      const locate = (index) => {
        let lo = 0, hi = textNodes.length - 1, mid
        while (lo <= hi) {
          mid = (lo + hi) >> 1
          const tn = textNodes[mid]
          if (index < tn.start) hi = mid - 1
          else if (index > tn.end) lo = mid + 1
          else return { node: tn.node, offset: index - tn.start }
        }
        const last = textNodes[textNodes.length - 1]
        return { node: last.node, offset: (last.end - last.start) }
      }

      // Utility: adjust index to previous word boundary
      const toPrevWordBoundary = (idx, minIndexExclusive) => {
        if (idx <= 0) return 0
        // Look back a few characters to find whitespace boundary
        const windowSize = 40
        const start = Math.max(0, idx - windowSize)
        const end = idx
        let s = ''
        // Build text substring from textNodes between start..end
        for (const tn of textNodes) {
          if (tn.end <= start || tn.start >= end) continue
          const from = Math.max(start, tn.start)
          const to = Math.min(end, tn.end)
          const sub = (tn.node.nodeValue || '').slice(from - tn.start, to - tn.start)
          s += sub
        }
        // Find last whitespace in window; if none, keep original idx
        for (let i = s.length - 1; i >= 0; i--) {
          if (/\s/.test(s[i])) {
            const pos = start + i
            // Ensure we don't go before current segment start
            if (pos <= minIndexExclusive) return Math.max(minIndexExclusive, idx)
            return pos
          }
        }
        return Math.max(minIndexExclusive, idx)
      }

      // Measurement container for fragments
      const measureDiv = document.createElement('div')
      measureDiv.style.position = 'absolute'
      measureDiv.style.visibility = 'hidden'
      measureDiv.style.pointerEvents = 'none'
      measureDiv.style.left = '-99999px'
      measureDiv.style.top = '0'
      measureDiv.style.width = `${contentWidth}px`
      const measStyle = getComputedStyle(meas)
      measureDiv.style.lineHeight = measStyle.lineHeight
      measureDiv.style.font = measStyle.font
      document.body.appendChild(measureDiv)

      let startIndex = 0
      let available = firstPageAvailable

      const shallowClone = () => blockEl.cloneNode(false)

      const buildFragmentHtmlUpTo = (endIndex) => {
        const range = document.createRange()
        const startLoc = locate(startIndex)
        const endLoc = locate(endIndex)
        range.setStart(startLoc.node, startLoc.offset)
        range.setEnd(endLoc.node, endLoc.offset)
        const fragment = range.cloneContents()
        const wrapper = shallowClone()
        wrapper.appendChild(fragment)
        return { html: wrapper.outerHTML, len: endIndex - startIndex }
      }

      while (startIndex < totalLength) {
        // Binary search the largest endIndex that fits within available height
        let lo = startIndex + 1
        let hi = totalLength
        let bestFit = startIndex + 1
        while (lo <= hi) {
          const mid = (lo + hi) >> 1
          const midHtml = buildFragmentHtmlUpTo(mid)
          measureDiv.innerHTML = midHtml
          const h = measureDiv.scrollHeight
          if (h <= available) {
            bestFit = mid
            lo = mid + 1
          } else {
            hi = mid - 1
          }
        }

        // Snap to previous word boundary to avoid cutting in the middle
        const snapped = toPrevWordBoundary(bestFit, startIndex)
        const pageFrag = buildFragmentHtmlUpTo(snapped)
        results.push(pageFrag)
        startIndex = snapped

        // For next segments of the same block, full page height is available
        available = pageHeight
      }

      document.body.removeChild(measureDiv)
      return results
    }

    // Allow browser to layout before measuring and paginating
    const raf = window.requestAnimationFrame(() => {
      const pageHeight = Math.max(1, viewer.clientHeight)
      const blocks = Array.from(meas.children)

      // Use the actual chunk boundaries we calculated earlier
      const boundaryPositions = chunkBoundaries.slice(1) // Skip first boundary (always 0)
      const boundarySet = new Set(boundaryPositions)
      const numChunks = chunkCount

      const newPages = []
      const starts = []
      const ends = []
      let currentHtml = ''
      let currentStartAbs = null
      let absOffset = 0
      let remaining = pageHeight

      // helper to push current page
      const pushPage = () => {
        newPages.push(currentHtml)
        starts.push(currentStartAbs == null ? absOffset : currentStartAbs)
        ends.push(absOffset - 1)
        currentHtml = ''
        currentStartAbs = null
        remaining = pageHeight
      }

      // Measure helper for fragments
      const hDiv = document.createElement('div')
      hDiv.style.position = 'absolute'
      hDiv.style.visibility = 'hidden'
      hDiv.style.pointerEvents = 'none'
      hDiv.style.left = '-99999px'
      hDiv.style.top = '0'
      hDiv.style.width = `${contentWidth}px`
      hDiv.style.lineHeight = vStyle.lineHeight
      hDiv.style.font = vStyle.font
      document.body.appendChild(hDiv)

      for (const block of blocks) {
        const blockTextLen = (block.textContent || '').length
        const blockHeight = block.offsetHeight

        // Try to fit the whole block by measuring combined HTML
        hDiv.innerHTML = currentHtml + block.outerHTML
        const combinedH = hDiv.scrollHeight
        if (combinedH <= pageHeight) {
          if (currentStartAbs == null) currentStartAbs = absOffset
          currentHtml += block.outerHTML
          absOffset += blockTextLen
          remaining = pageHeight - combinedH
          continue
        }

        // Split the block across pages
        const parts = splitBlockByHeight(block, Math.max(1, remaining), pageHeight)

        if (parts.length > 0) {
          if (currentStartAbs == null) currentStartAbs = absOffset
          currentHtml += parts[0].html
          absOffset += parts[0].len
          // Filled current page
          pushPage()
        }

        // Middle full pages
        for (let i = 1; i < parts.length - 1; i++) {
          const frag = parts[i]
          currentHtml = frag.html
          currentStartAbs = absOffset
          absOffset += frag.len
          pushPage()
        }

        // Last partial page
        if (parts.length > 1) {
          const frag = parts[parts.length - 1]
          currentHtml = frag.html
          currentStartAbs = absOffset
          absOffset += frag.len
          // compute remaining space for the last fragment
          hDiv.innerHTML = frag.html
          const h = hDiv.scrollHeight
          remaining = Math.max(0, pageHeight - h)
        }
      }

      // Push trailing page if any content
      if (currentHtml !== '') {
        pushPage()
      }

      document.body.removeChild(hDiv)

      setPagesHtml(newPages)
      setPageStartAbs(starts)
      setPageEndAbs(ends)
      setTotalPages(Math.max(1, newPages.length))
      setCurrentPage((p) => Math.min(p, Math.max(0, newPages.length - 1)))

      // Compute chunk ranges per page
      const findChunkIndexAt = (pos) => {
        // number of boundaries <= pos
        let lo = 0, hi = boundaryPositions.length - 1, ans = -1
        while (lo <= hi) {
          const mid = (lo + hi) >> 1
          if (boundaryPositions[mid] <= pos) { ans = mid; lo = mid + 1 } else { hi = mid - 1 }
        }
        return ans + 1
      }

      const boundaryIsAt = (pos) => boundarySet.has(pos)

      const ranges = newPages.map((_, i) => {
        let s = starts[i]
        let e = ends[i]
        if (s > e) return { startChunk: 0, endChunk: 0 }
        while (boundaryIsAt(s) && s < e) s += 1
        let eAdj = boundaryIsAt(e) ? e - 1 : e
        if (eAdj < s) eAdj = s

        let startChunk = findChunkIndexAt(s)
        let endChunk = findChunkIndexAt(eAdj)

        // If page ends exactly at end of a chunk (char right before boundary), move to next chunk
        const nextBoundaryPos = boundaryPositions[endChunk] ?? Infinity
        if (eAdj === nextBoundaryPos - 1) {
          endChunk = Math.min(endChunk + 1, numChunks)
        }

        return { startChunk, endChunk }
      })
      setPageChunkRanges(ranges)
    })

    return () => window.cancelAnimationFrame(raf)
  }, [markdown, loading, viewerHeight, controlsHeight])

  // Observe bottom controls height so we don't overlap content
  React.useLayoutEffect(() => {
    const el = controlsRef.current
    if (!el) return
    const update = () => setControlsHeight(el.clientHeight || 0)
    update()
    let ro
    if ('ResizeObserver' in window) {
      ro = new ResizeObserver(update)
      ro.observe(el)
    }
    window.addEventListener('resize', update)
    return () => {
      if (ro) ro.disconnect()
      window.removeEventListener('resize', update)
    }
  }, [loading])

  // Reset scroll and page indices when document changes
  React.useEffect(() => {
    const el = viewerRef.current
    if (el) el.scrollTo({ top: 0, behavior: 'auto' })
    setCurrentPage(0)
    setPdfCurrentPage(0)
  }, [id, markdown])

  // Reset PDF page when switching to PDF mode
  React.useEffect(() => {
    if (viewMode === 'pdf') {
      setPdfCurrentPage(0)
    }
  }, [viewMode])

  // Update input values when pages change
  React.useEffect(() => {
    setMdPageInput('')
  }, [currentPage])

  React.useEffect(() => {
    setPdfPageInput('')
  }, [pdfCurrentPage])

  const sendTrackForCurrentPage = async () => {
    try {
      if (viewMode === 'markdown') {
        const range = pageChunkRanges[currentPage]
        if (!range) return
        await trackPage({ 
          docId: Number(id), 
          chunkStart: range.startChunk,
          chunkEnd: range.endChunk,
          readerType: 'md'
        })
      } else {
        // PDF mode - track by page number
        await trackPage({ 
          docId: Number(id), 
          pageNumber: pdfCurrentPage + 1, // 1-indexed for backend
          readerType: 'pdf'
        })
      }
    } catch (e) {
      console.error('Tracking failed', e)
    }
  }

  const handlePrev = async () => {
    if (viewMode === 'markdown') {
      const prev = Math.max(0, currentPage - 1)
      if (prev !== currentPage) {
        // Track the page we're leaving (current page)
        await sendTrackForCurrentPage()
        setCurrentPage(prev)
      }
    } else {
      // PDF mode
      const prev = Math.max(0, pdfCurrentPage - 1)
      if (prev !== pdfCurrentPage) {
        await sendTrackForCurrentPage()
        setPdfCurrentPage(prev)
      }
    }
  }

  const handleNext = async () => {
    if (viewMode === 'markdown') {
      const next = Math.min(totalPages - 1, currentPage + 1)
      if (next !== currentPage) {
        // Track the page we're leaving (current page)
        await sendTrackForCurrentPage()
        setCurrentPage(next)
      }
    } else {
      // PDF mode
      const next = Math.min(pdfTotalPages - 1, pdfCurrentPage + 1)
      if (next !== pdfCurrentPage) {
        await sendTrackForCurrentPage()
        setPdfCurrentPage(next)
      }
    }
  }

  const handleMdPageInput = async (e) => {
    if (e.key === 'Enter') {
      const pageNum = parseInt(mdPageInput)
      if (pageNum >= 1 && pageNum <= totalPages) {
        await sendTrackForCurrentPage()
        setCurrentPage(pageNum - 1) // Convert to 0-based index
        setMdPageInput('')
      }
    }
  }

  const handlePdfPageInput = async (e) => {
    if (e.key === 'Enter') {
      const pageNum = parseInt(pdfPageInput)
      if (pageNum >= 1 && pageNum <= pdfTotalPages) {
        await sendTrackForCurrentPage()
        setPdfCurrentPage(pageNum - 1) // Convert to 0-based index
        setPdfPageInput('')
      }
    }
  }

  // Track when user leaves the page or navigates back/away
  React.useEffect(() => {
    const handleBeforeUnload = () => {
      if (viewMode === 'markdown') {
        const range = pageChunkRanges[currentPage]
        if (!range) return
        // Fire-and-forget; navigator.sendBeacon preferable but our API requires auth header
        trackPage({ 
          docId: Number(id), 
          chunkStart: range.startChunk,
          chunkEnd: range.endChunk,
          readerType: 'md'
        }).catch(() => {})
      } else {
        // PDF mode
        trackPage({ 
          docId: Number(id), 
          pageNumber: pdfCurrentPage + 1,
          readerType: 'pdf'
        }).catch(() => {})
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [id, currentPage, pageChunkRanges, viewMode, pdfCurrentPage])


  return (
    <div style={{ position: 'fixed', inset: 0, background: '#fff' }}>
      {/* Menu button */}
      <button
        className="btn btn-secondary"
        onClick={() => setDrawerOpen(true)}
        style={{ position: 'fixed', top: '1rem', left: '1rem', zIndex: 1001 }}
      >
        Menu
      </button>

      {/* Reader name (visually subtle) */}
      <div style={{ position: 'fixed', top: '1.2rem', left: '5.5rem', right: '12rem', color: '#6c757d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {name}
        </div>

      {/* View mode toggle */}
      <div style={{ position: 'fixed', top: '1rem', right: '1rem', zIndex: 1001 }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            className={`btn ${viewMode === 'markdown' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewMode('markdown')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 0.75rem' }}
          >
            MD
          </button>
          <button
            className={`btn ${viewMode === 'pdf' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewMode('pdf')}
            style={{ fontSize: '0.875rem', padding: '0.5rem 0.75rem' }}
          >
            PDF
          </button>
        </div>
      </div>

      {/* Reader viewport */}
      <div style={{ position: 'absolute', top: '4rem', left: 0, right: 0, bottom: `${controlsHeight}px`, padding: '0 1rem' }}>
          {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <div className="spinner"></div>
            </div>
          ) : viewMode === 'markdown' ? (
            <>
              <div
                ref={viewerRef}
                style={{
                  lineHeight: 1.6,
                height: '100%',
                overflow: 'auto',
                  paddingRight: '0.5rem',
                  backgroundAttachment: 'local',
                }}
                dangerouslySetInnerHTML={{ __html: pagesHtml[currentPage] || '' }}
              />

            {/* Hidden measurement container */}
            <div
              ref={measureRef}
              aria-hidden="true"
              style={{ position: 'absolute', left: '-99999px', top: 0, visibility: 'hidden', pointerEvents: 'none' }}
            >
              <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {markdown}
              </ReactMarkdown>
            </div>
          </>
        ) : (
          /* PDF View */
          <PDFViewer 
            pdfUrl={pdfUrl}
            currentPage={pdfCurrentPage}
            onPageChange={setPdfCurrentPage}
            onTotalPagesChange={setPdfTotalPages}
          />
        )}
              </div>

      {/* Bottom controls - show for both views */}
      <div ref={controlsRef} style={{ position: 'fixed', left: 0, right: 0, bottom: 0, padding: '0.75rem 1rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button 
            className="btn btn-secondary" 
            onClick={handlePrev} 
            disabled={viewMode === 'markdown' ? currentPage === 0 : pdfCurrentPage === 0}
          >
            Prev
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {viewMode === 'markdown' ? (
              <>
                <span style={{ color: '#6c757d' }}>
                  Page {Math.min(totalPages, Math.max(1, currentPage + 1))} / {Math.max(1, totalPages)}
                  {pageChunkRanges[currentPage] ? ` · chunks ${pageChunkRanges[currentPage].startChunk}–${pageChunkRanges[currentPage].endChunk}` : ''}
                </span>
                <input
                  type="number"
                  value={mdPageInput}
                  onChange={(e) => setMdPageInput(e.target.value)}
                  onKeyDown={handleMdPageInput}
                  placeholder="Go to page"
                  min="1"
                  max={totalPages}
                  style={{
                    width: '80px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.875rem',
                    border: '1px solid #6c757d',
                    borderRadius: '4px',
                    textAlign: 'center'
                  }}
                />
              </>
            ) : (
              <>
                <span style={{ color: '#6c757d' }}>
                  PDF Page {pdfCurrentPage + 1} / {pdfTotalPages}
                </span>
                <input
                  type="number"
                  value={pdfPageInput}
                  onChange={(e) => setPdfPageInput(e.target.value)}
                  onKeyDown={handlePdfPageInput}
                  placeholder="Go to page"
                  min="1"
                  max={pdfTotalPages}
                  style={{
                    width: '80px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.875rem',
                    border: '1px solid #6c757d',
                    borderRadius: '4px',
                    textAlign: 'center'
                  }}
                />
              </>
            )}
          </div>
          
          <button 
            className="btn btn-primary" 
            onClick={handleNext} 
            disabled={viewMode === 'markdown' ? currentPage >= totalPages - 1 : pdfCurrentPage >= pdfTotalPages - 1}
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



