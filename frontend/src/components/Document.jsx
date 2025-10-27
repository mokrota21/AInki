import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import toast from 'react-hot-toast'
import { fetchFileContent, trackPage, api } from '../services/api'
import PDFViewer from './PDFViewer'
import QuizPopup from './QuizPopup'
import 'katex/dist/katex.min.css'

function Document() {
  const SENTINEL = '\u2063'
  const { id } = useParams()
  const navigate = useNavigate()
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
  const [viewMode, setViewMode] = React.useState('pdf') // 'markdown' or 'pdf'
  const [pdfCurrentPage, setPdfCurrentPage] = React.useState(0)
  const [pdfTotalPages, setPdfTotalPages] = React.useState(1)
  const [pdfUrl, setPdfUrl] = React.useState('')
  const [mdPageInput, setMdPageInput] = React.useState('')
  const [pdfPageInput, setPdfPageInput] = React.useState('')
  const [pdfSliderValue, setPdfSliderValue] = React.useState(1)
  const [pageMastery, setPageMastery] = React.useState([])
  
  // Quiz popup state
  const [quizPopupOpen, setQuizPopupOpen] = React.useState(false)
  const [quizTimer, setQuizTimer] = React.useState(null)
  const [lastQuizTime, setLastQuizTime] = React.useState(Date.now())
  const lastQuizTimeRef = React.useRef(Date.now())
  const pendingLockRef = React.useRef(false)
  const quizOpenRef = React.useRef(false)
  const [quizItems, setQuizItems] = React.useState([])
  const [quizButtonLoading, setQuizButtonLoading] = React.useState(false)
  const pageEnterTimeRef = React.useRef(Date.now())
  const MIN_DWELL_MS = 30000

  // Configurable pending timer (defaults with overrides)
  const getNumber = (val, fallback) => {
    const num = Number(val)
    return Number.isFinite(num) && num > 0 ? num : fallback
  }
  const defaultPendingCheckIntervalMs = getNumber(import.meta?.env?.VITE_PENDING_CHECK_INTERVAL_MS, 10000)
  const defaultPendingThresholdMs = getNumber(import.meta?.env?.VITE_PENDING_THRESHOLD_MS, 6000000) // Change this later
  const [pendingCheckIntervalMs, setPendingCheckIntervalMs] = React.useState(() =>
    getNumber(localStorage.getItem('AINKI_PENDING_CHECK_INTERVAL_MS'), defaultPendingCheckIntervalMs)
  )
  const [pendingThresholdMs, setPendingThresholdMs] = React.useState(() =>
    getNumber(localStorage.getItem('AINKI_PENDING_THRESHOLD_MS'), defaultPendingThresholdMs)
  )

  // Expose runtime override API for tests: window.__AInkiSetPendingTimer({ checkIntervalMs, thresholdMs })
  React.useEffect(() => {
    window.__AInkiSetPendingTimer = (config = {}) => {
      if (config.checkIntervalMs !== undefined) {
        const v = getNumber(config.checkIntervalMs, pendingCheckIntervalMs)
        setPendingCheckIntervalMs(v)
      }
      if (config.thresholdMs !== undefined) {
        const v = getNumber(config.thresholdMs, pendingThresholdMs)
        setPendingThresholdMs(v)
      }
      if (config.persist) {
        if (config.checkIntervalMs !== undefined) localStorage.setItem('AINKI_PENDING_CHECK_INTERVAL_MS', String(config.checkIntervalMs))
        if (config.thresholdMs !== undefined) localStorage.setItem('AINKI_PENDING_THRESHOLD_MS', String(config.thresholdMs))
      }
    }
    return () => { try { delete window.__AInkiSetPendingTimer } catch (_) {} }
  }, [pendingCheckIntervalMs, pendingThresholdMs])

  // Mirror popup visibility in a ref for timer closure
  React.useEffect(() => {
    quizOpenRef.current = quizPopupOpen
  }, [quizPopupOpen])
  
  // Track only on explicit page change via buttons

  React.useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await fetchFileContent(id)
        const docName = data?.name || 'Document'
        const folder = data?.folder || ''
        const chunks = Array.isArray(data?.chunks) ? data.chunks : []
        
        // Set PDF URL - now served from backend storage by doc_id
        const pdfUrl = `/api/get_file?doc_id=${Number(id)}`
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
  }, [markdown, loading, viewerHeight])

  // Observe bottom controls height so we don't overlap content
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
    // Reset dwell timer on view change
    pageEnterTimeRef.current = Date.now()
  }, [viewMode])

  // Update input values when pages change
  React.useEffect(() => {
    setMdPageInput('')
  }, [currentPage])

  React.useEffect(() => {
    setPdfPageInput('')
  }, [pdfCurrentPage])

  // Sync slider with current PDF page and total pages
  React.useEffect(() => {
    setPdfSliderValue(Math.min(pdfTotalPages, Math.max(1, pdfCurrentPage + 1)))
  }, [pdfCurrentPage, pdfTotalPages])

  // Fetch per-page mastery once per document id
  React.useEffect(() => {
    let cancelled = false
    const fetchMastery = async () => {
      try {
        const response = await api.get('/mastery', { params: { doc_id: Number(id) } })
        if (!cancelled) {
          const data = Array.isArray(response?.data) ? response.data : []
          setPageMastery(data)
        }
      } catch (e) {
        console.error('Failed to load page mastery', e)
        if (!cancelled) setPageMastery([])
      }
    }
    if (id) fetchMastery()
    return () => { cancelled = true }
  }, [id])

  // Helpers for mastery visualization
  const getMasteryForPage = (pageIndex0) => {
    // Prefer exact length match; else try 1-indexed arrays; else fallback 0
    if (Array.isArray(pageMastery)) {
      if (pageMastery.length === pdfTotalPages) return pageMastery[pageIndex0]
      if (pageMastery.length === pdfTotalPages + 1) return pageMastery[pageIndex0 + 1]
      return pageMastery[pageIndex0]
    }
    return undefined
  }

  const getMasteryColor = (value) => {
    const v = typeof value === 'number' && isFinite(value) ? Math.max(0, Math.min(1, value)) : null
    if (v === null) return '#ced4da' // muted gray when unknown
    const hue = v * 120 // 0=red, 120=green
    return `hsl(${hue}, 70%, 45%)`
  }

  const navigateToPdfPage = async (target1Indexed) => {
    const target = Math.min(pdfTotalPages, Math.max(1, target1Indexed))
    if (target - 1 === pdfCurrentPage) return
    await sendTrackForCurrentPage()
    setPdfCurrentPage(target - 1)
    setPdfSliderValue(target)
    pageEnterTimeRef.current = Date.now()
  }

  const sendTrackForCurrentPage = async () => {
    try {
      // Require at least 30s dwell time before tracking
      const dwellMs = Date.now() - pageEnterTimeRef.current
      if (dwellMs < MIN_DWELL_MS) return
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
        pageEnterTimeRef.current = Date.now()
      }
    } else {
      // PDF mode
      const prev = Math.max(0, pdfCurrentPage - 1)
      if (prev !== pdfCurrentPage) {
        await sendTrackForCurrentPage()
        setPdfCurrentPage(prev)
        pageEnterTimeRef.current = Date.now()
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
        pageEnterTimeRef.current = Date.now()
      }
    } else {
      // PDF mode
      const next = Math.min(pdfTotalPages - 1, pdfCurrentPage + 1)
      if (next !== pdfCurrentPage) {
        await sendTrackForCurrentPage()
        setPdfCurrentPage(next)
        pageEnterTimeRef.current = Date.now()
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
        pageEnterTimeRef.current = Date.now()
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
        pageEnterTimeRef.current = Date.now()
      }
    }
  }

  // Track when user leaves the page or navigates back/away
  React.useEffect(() => {
    const handleBeforeUnload = () => {
      if (viewMode === 'markdown') {
        const range = pageChunkRanges[currentPage]
        if (!range) return
        // Dwell gating
        const dwellMs = Date.now() - pageEnterTimeRef.current
        if (dwellMs >= MIN_DWELL_MS) {
          // Fire-and-forget; navigator.sendBeacon preferable but our API requires auth header
          trackPage({ 
            docId: Number(id), 
            chunkStart: range.startChunk,
            chunkEnd: range.endChunk,
            readerType: 'md'
          }).catch(() => {})
        }
      } else {
        // PDF mode
        const dwellMs = Date.now() - pageEnterTimeRef.current
        if (dwellMs >= MIN_DWELL_MS) {
          trackPage({ 
            docId: Number(id), 
            pageNumber: pdfCurrentPage + 1,
            readerType: 'pdf'
          }).catch(() => {})
        }
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [id, currentPage, pageChunkRanges, viewMode, pdfCurrentPage])

  // Quiz popup timer logic
  React.useEffect(() => {
    if (loading) return

    // Clear existing timer
    if (quizTimer) {
      clearInterval(quizTimer)
    }

    // Set up new timer for 1 minute intervals
    const timer = setInterval(() => {
      // Do not make pending requests while quiz popup is visible
      if (quizOpenRef.current) return
      // Do not make another call while lock is held
      if (pendingLockRef.current) return
      const now = Date.now()
      const timeSinceLastQuiz = now - lastQuizTimeRef.current
      
      // Check for pending items when threshold elapsed
      if (timeSinceLastQuiz >= pendingThresholdMs) {
        checkPendingAndShowPopup()
      }
    }, pendingCheckIntervalMs) // Check on configured interval

    setQuizTimer(timer)

    return () => {
      if (timer) clearInterval(timer)
    }
  }, [loading, pendingCheckIntervalMs, pendingThresholdMs])

  // Clean up timer on unmount
  React.useEffect(() => {
    return () => {
      if (quizTimer) {
        clearInterval(quizTimer)
      }
    }
  }, [quizTimer])

  // Check if there are pending items before showing popup
  const checkPendingAndShowPopup = async () => {
    // Do not make pending requests while quiz popup is visible
    if (quizOpenRef.current) return
    // Check if lock is already acquired
    if (pendingLockRef.current) return

    try {
      // Acquire lock
      pendingLockRef.current = true
      
      const response = await api.get('/pending', { params: { doc_id: Number(id) } })
      if (response.data && response.data.length > 0) {
        // Mark quiz as open to prohibit further calls before state flushes
        quizOpenRef.current = true
        setQuizItems(response.data)
        setQuizPopupOpen(true)
      } else {
        // No items returned; reset timer so next check happens in one minute
        const now = Date.now()
        setLastQuizTime(now)
        lastQuizTimeRef.current = now
      }
    } catch (error) {
      console.error('Failed to check pending items:', error)
      // On error, still reset timer to prevent repeated failed requests
      const now = Date.now()
      setLastQuizTime(now)
      lastQuizTimeRef.current = now
    } finally {
      // Always release lock
      pendingLockRef.current = false
    }
  }

  // Fetch assigned items explicitly (used by Quiz button)
  const fetchAssignedAndShowPopup = async () => {
    if (quizOpenRef.current) return
    if (pendingLockRef.current) return

    try {
      pendingLockRef.current = true
      const response = await api.get('/assigned', { params: { doc_id: Number(id) } })
      if (response.data && response.data.length > 0) {
        quizOpenRef.current = true
        setQuizItems(response.data)
        setQuizPopupOpen(true)
      } else {
        const now = Date.now()
        setLastQuizTime(now)
        lastQuizTimeRef.current = now
        toast.error('You need to first create quiz before pressing on this button! Go back to dashboard and generate quiz for this document!')
      }
    } catch (error) {
      console.error('Failed to load assigned items:', error)
      toast.error('Failed to load assigned items')
    } finally {
      pendingLockRef.current = false
    }
  }

  // Debug function to manually trigger quiz popup
  const triggerQuizPopup = async () => {
    if (quizOpenRef.current) return
    if (pendingLockRef.current) return
    try {
      setQuizButtonLoading(true)
      await fetchAssignedAndShowPopup()
    } finally {
      setQuizButtonLoading(false)
    }
  }

  // Handle quiz popup close
  const handleQuizPopupClose = () => {
    setQuizPopupOpen(false)
    // When popup becomes invisible, restart timer baseline
    const now = Date.now()
    setLastQuizTime(now)
    lastQuizTimeRef.current = now
    setQuizItems([])
  }

  // Handle quiz completion
  const handleQuizComplete = () => {
    const now = Date.now()
    setLastQuizTime(now) // Reset timer after quiz completion
    lastQuizTimeRef.current = now
    // Popup will close shortly after via onComplete->onClose
  }

  return (
    <div className="reader-shell">
      <div className="reader-hover-zone reader-hover-zone--top" />
      <div className="reader-controls reader-controls--top">
        <div className="reader-controls__bar reader-controls__bar--top">
          <button
            className="btn btn-secondary reader-back-button"
            onClick={() => navigate('/dashboard')}
          >
            ← Back
          </button>
          <div className="reader-title" title={name}>
            {name}
          </div>
          <div className="reader-actions">
            <button
              className="btn reader-quiz-button"
              onClick={triggerQuizPopup}
              disabled={quizButtonLoading}
              title="Trigger Quiz Popup"
            >
              {quizButtonLoading ? 'Loading…' : '🧠 Quiz'}
            </button>
            <button
              className={`btn reader-toggle ${viewMode === 'markdown' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('markdown')}
            >
              MD
            </button>
            <button
              className={`btn reader-toggle ${viewMode === 'pdf' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('pdf')}
            >
              PDF
            </button>
          </div>
        </div>
      </div>

      <div className="reader-stage">
        <div className="reader-stage__surface">
          {loading ? (
            <div className="reader-stage__loading">
              <div className="spinner"></div>
            </div>
          ) : viewMode === 'markdown' ? (
            <>
              <div
                ref={viewerRef}
                className="reader-stage__scroll"
                dangerouslySetInnerHTML={{ __html: pagesHtml[currentPage] || '' }}
              />
              <div
                ref={measureRef}
                aria-hidden="true"
                className="reader-stage__measure"
              >
                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {markdown}
                </ReactMarkdown>
              </div>
            </>
          ) : (
            <div className="reader-stage__pdf">
              <div className="reader-stage__pdf-viewer">
                <PDFViewer
                  pdfUrl={pdfUrl}
                  currentPage={pdfCurrentPage}
                  onPageChange={(p) => {
                    setPdfCurrentPage(p)
                    pageEnterTimeRef.current = Date.now()
                  }}
                  onTotalPagesChange={(tp) => {
                    setPdfTotalPages(tp)
                    setPdfSliderValue(Math.min(tp, Math.max(1, pdfCurrentPage + 1)))
                  }}
                />
              </div>
              <div className="reader-stage__pdf-master">
                <div className="reader-stage__pdf-master-bar">
                  {Array.from({ length: Math.max(1, pdfTotalPages) }, (_, i) => {
                    const mastery = getMasteryForPage(i)
                    const color = getMasteryColor(mastery)
                    const isCurrent = i === pdfCurrentPage
                    return (
                      <div
                        key={`mastery-${i}`}
                        onClick={() => navigateToPdfPage(i + 1)}
                        title={`Page ${i + 1}${typeof mastery === 'number' ? ` · ${(mastery * 100).toFixed(0)}%` : ''}`}
                        className={`reader-stage__pdf-master-cell${isCurrent ? ' is-active' : ''}`}
                        style={{ background: color }}
                      />
                    )
                  })}
                </div>
              </div>
              <div className="reader-stage__pdf-slider">
                <input
                  type="range"
                  min={1}
                  max={Math.max(1, pdfTotalPages)}
                  value={pdfSliderValue}
                  onChange={(e) => setPdfSliderValue(parseInt(e.target.value))}
                  onMouseUp={async () => { await navigateToPdfPage(pdfSliderValue) }}
                  onTouchEnd={async () => { await navigateToPdfPage(pdfSliderValue) }}
                />
                <div className="reader-stage__pdf-slider-meta">
                  <span>1</span>
                  <span>Page {pdfSliderValue} / {Math.max(1, pdfTotalPages)}</span>
                  <span>{Math.max(1, pdfTotalPages)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="reader-hover-zone reader-hover-zone--bottom" />
      <div className="reader-controls reader-controls--bottom">
        <div className="reader-controls__bar reader-controls__bar--bottom">
          <button
            className="btn btn-secondary"
            onClick={handlePrev}
            disabled={viewMode === 'markdown' ? currentPage === 0 : pdfCurrentPage === 0}
          >
            Prev
          </button>

          <div className="reader-page-info">
            {viewMode === 'markdown' ? (
              <>
                <span>
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
                  className="reader-page-input"
                />
              </>
            ) : (
              <>
                <span>
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
                  className="reader-page-input"
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

      <QuizPopup
        isOpen={quizPopupOpen}
        items={quizItems}
        onClose={handleQuizPopupClose}
        onComplete={handleQuizComplete}
      />
    </div>
  )
}

export default Document



