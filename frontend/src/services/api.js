import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Fetch user books
export async function fetchUserBooks() {
  const response = await api.get('/fetch-user-books')
  return response.data
}

// Add book
export async function addBook(file, force = false) {
  const formData = new FormData()
  formData.append('book', file)
  formData.append('force', force)
  const response = await api.post('/add-book', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// Get book file
export function getBookUrl(filename) {
  return `${API_BASE_URL}/get-book?filename=${encodeURIComponent(filename)}`
}

// Extract knowledge from a book
export async function extractKnowledge(docId) {
  // FastAPI accepts query parameters in POST requests
  const response = await api.post(`/extract-knowledge?doc_id=${docId}`)
  return response.data
}

// Get background task status
export async function getBackgroundTask(taskId) {
  const response = await api.get('/get-background-task', {
    params: { task_id: taskId }
  })
  return response.data
}

// Get book questions for a specific page
export async function getBookQuestions(docId, pageNo) {
  const response = await api.get('/get-book-questions', {
    params: { doc_id: docId, page_no: pageNo }
  })
  return response.data
}
