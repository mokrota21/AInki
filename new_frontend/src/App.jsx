import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Dashboard from './components/Dashboard'
import BookReader from './components/BookReader'

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/read/:docId/:filename" element={<BookReader />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
