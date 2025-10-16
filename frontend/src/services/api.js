import axios from 'axios'

// Use Vite's injected env; fallback to proxy path
const API_BASE_URL = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Convenience helpers
export async function fetchFileContent(docId) {
  // Backend implemented as GET /api/file_content?doc_id=ID
  const response = await api.get(`/file_content`, { params: { doc_id: docId } })
  return response.data
}

// Track reading progress - supports both MD and PDF views
export async function trackPage({ docId, chunkEnd, chunkStart, pageNumber, readerType = 'md' }) {
  if (readerType === 'md') {
    // For markdown: send both start and end chunk indexes
    return api.post(`/track`, {
      doc_id: docId,
      track_element_end_idx: [chunkStart, chunkEnd],
      frontend_reader_type: 'md'
    })
  } else {
    // For PDF: send only page number
    return api.post(`/track`, {
      doc_id: docId,
      track_element_end_idx: pageNumber,
      frontend_reader_type: 'pdf'
    })
  }
}

// Quiz generation endpoints
export async function getQuizParameters() {
  return api.post('/extract_objects_parameter')
}

export async function getPriceApproximation(docId, promptKey = "general_textbook_prompt", modelName = "gpt-5-nano") {
  return api.post(`/price_approximation?doc_id=${docId}&prompt_key=${promptKey}&model_name=${modelName}`)
}

export async function extractObjects(docId, promptKey = "general_textbook_prompt", additionalParams = {}) {
  const queryParams = new URLSearchParams({
    doc_id: docId,
    prompt_key: promptKey,
    kwargs: '', // FastAPI requires this parameter due to **kwargs in the function signature
    ...additionalParams
  })
  return api.post(`/extract_objects?${queryParams}`)
}