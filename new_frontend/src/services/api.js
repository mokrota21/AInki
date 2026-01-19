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
export async function addBook(file) {
  const formData = new FormData()
  formData.append('book', file)
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
