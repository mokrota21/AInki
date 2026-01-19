import React, { useState, useEffect, useRef } from 'react'
import { Search, Settings, BookOpen, Flame, Headphones, Plus } from 'lucide-react'
import { fetchUserBooks, addBook, getBookUrl } from '../services/api'
import toast from 'react-hot-toast'
import './Dashboard.css'

function Dashboard() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedBook, setSelectedBook] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadBooks()
  }, [])

  const loadBooks = async () => {
    try {
      setLoading(true)
      const data = await fetchUserBooks()
      // Backend now returns plain dicts, so we can use them directly
      setBooks(data)
    } catch (error) {
      toast.error('Failed to load books: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleAddBook = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    try {
      await addBook(file)
      toast.success('Book added successfully!')
      loadBooks()
    } catch (error) {
      toast.error('Failed to add book: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleBookClick = (book) => {
    const fileUrl = getBookUrl(book.file_name)
    setSelectedBook({ ...book, url: fileUrl })
  }

  const getBookColor = (index) => {
    const colors = ['orange', 'green', 'blue']
    return colors[index % colors.length]
  }

  const calculateProgress = (book) => {
    // Dummy progress calculation - replace with real data later
    return Math.floor(Math.random() * 60 + 20) // 20-80%
  }

  const calculateMastery = (book) => {
    // Dummy mastery calculation - replace with real data later
    return Math.floor(Math.random() * 40 + 40) // 40-80%
  }

  const calculateConcepts = (book) => {
    // Dummy concept calculation - replace with real data later
    const total = book.pages_total * 3
    const learned = Math.floor(total * (calculateProgress(book) / 100))
    return { learned, total }
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <BookOpen className="logo-icon" />
            <span className="logo-text">LearnFlow</span>
          </div>
        </div>
        <div className="header-right">
          <div className="search-bar">
            <Search className="search-icon" size={20} />
            <input type="text" placeholder="Search books..." />
          </div>
          <button className="settings-btn">
            <Settings size={20} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="dashboard-content">
        {/* Left Panel - Your Library */}
        <div className="library-panel">
          <div className="panel-header">
            <h2>Your Library</h2>
            <button 
              className="add-book-btn"
              onClick={handleAddBook}
              disabled={uploading}
            >
              <Plus size={18} />
              Add Book
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>

          {loading ? (
            <div className="loading">Loading books...</div>
          ) : books.length === 0 ? (
            <div className="empty-state">No books yet. Add your first book!</div>
          ) : (
            <div className="books-list">
              {books.map((book, index) => {
                const color = getBookColor(index)
                const progress = calculateProgress(book)
                const mastery = calculateMastery(book)
                const concepts = calculateConcepts(book)
                const date = new Date(book.created_at).toLocaleDateString('en-US', {
                  month: 'numeric',
                  day: 'numeric',
                  year: 'numeric'
                })

                return (
                  <div
                    key={book.doc_id}
                    className={`book-card book-card-${color}`}
                    onClick={() => handleBookClick(book)}
                  >
                    <div className="book-icon">
                      <BookOpen size={24} />
                    </div>
                    <div className="book-info">
                      <h3 className="book-title">{book.file_name.replace(/\.[^/.]+$/, '')}</h3>
                      <p className="book-author">Author Name</p>
                      <div className="book-progress">
                        <div className="progress-label">Reading Progress</div>
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <div className="progress-stats">
                          <span>{concepts.learned}/{concepts.total} concepts</span>
                          <span className="progress-date">{date}</span>
                        </div>
                      </div>
                    </div>
                    <div className="book-mastery">
                      <div className="mastery-circle">
                        <svg className="mastery-svg" viewBox="0 0 100 100">
                          <circle
                            className="mastery-bg"
                            cx="50"
                            cy="50"
                            r="45"
                          />
                          <circle
                            className="mastery-progress"
                            cx="50"
                            cy="50"
                            r="45"
                            strokeDasharray={`${mastery * 2.827} 283`}
                          />
                        </svg>
                        <div className="mastery-text">{mastery}%</div>
                      </div>
                      <div className="mastery-label">Mastery</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="right-panel">
          {/* Today's Goals */}
          <div className="goals-panel">
            <div className="panel-header">
              <h2>Today's Goals</h2>
              <div className="streak-badge">
                <Flame size={16} />
                <span>7 day streak</span>
              </div>
            </div>
            <div className="goals-content">
              <div className="goal-item">
                <div className="goal-icon">
                  <BookOpen size={20} />
                </div>
                <div className="goal-info">
                  <div className="goal-label">Pages Read</div>
                  <div className="goal-progress-bar">
                    <div className="goal-progress-fill" style={{ width: '60%' }} />
                  </div>
                  <div className="goal-stats">12/20</div>
                </div>
              </div>
              <div className="goal-item">
                <div className="goal-icon">
                  <Headphones size={20} />
                </div>
                <div className="goal-info">
                  <div className="goal-label">Questions Reviewed</div>
                  <div className="goal-progress-bar">
                    <div className="goal-progress-fill" style={{ width: '72%' }} />
                  </div>
                  <div className="goal-stats">18/25</div>
                </div>
              </div>
            </div>
            <div className="wip-badge">WIP</div>
          </div>

          {/* Concept Map */}
          <div className="concept-map-panel">
            <div className="panel-header">
              <h2>Concept Map</h2>
            </div>
            <div className="concept-map-content">
              {/* Empty div for future implementation */}
            </div>
          </div>
        </div>
      </div>

      {/* Book Viewer Modal */}
      {selectedBook && (
        <div className="book-modal" onClick={() => setSelectedBook(null)}>
          <div className="book-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setSelectedBook(null)}>×</button>
            <iframe
              src={selectedBook.url}
              className="book-iframe"
              title={selectedBook.file_name}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
