import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { X, ChevronLeft, ChevronRight, Brain, Lightbulb } from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
import { getBookUrl, getBookQuestions } from '../services/api'
import toast from 'react-hot-toast'
import './BookReader.css'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

function BookReader() {
  const { docId, filename } = useParams()
  const navigate = useNavigate()
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [questions, setQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [showQuiz, setShowQuiz] = useState(false)
  const [loadingQuestions, setLoadingQuestions] = useState(false)
  const [userAnswer, setUserAnswer] = useState('')
  const [showHint, setShowHint] = useState(false)
  const [pageInput, setPageInput] = useState('1')

  const pdfUrl = getBookUrl(decodeURIComponent(filename))

  const onDocumentLoadSuccess = ({ numPages }) => {
    setTotalPages(numPages)
  }

  const goToPage = (pageNum) => {
    const page = Math.max(1, Math.min(pageNum, totalPages))
    setCurrentPage(page)
    setPageInput(String(page))
  }

  const handlePageInputChange = (e) => {
    setPageInput(e.target.value)
  }

  const handlePageInputSubmit = (e) => {
    e.preventDefault()
    const pageNum = parseInt(pageInput, 10)
    if (!isNaN(pageNum)) {
      goToPage(pageNum)
    }
  }

  const handleStartQuiz = async () => {
    setLoadingQuestions(true)
    try {
      const data = await getBookQuestions(docId, currentPage)
      if (data.length === 0) {
        toast.error('No questions available for this page yet')
        return
      }
      setQuestions(data)
      setCurrentQuestionIndex(0)
      setShowQuiz(true)
      setUserAnswer('')
      setShowHint(false)
    } catch (error) {
      toast.error('Failed to load questions: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingQuestions(false)
    }
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
      setUserAnswer('')
      setShowHint(false)
    } else {
      setShowQuiz(false)
      toast.success('Quiz completed!')
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
      setUserAnswer('')
      setShowHint(false)
    }
  }

  const currentQuestion = questions[currentQuestionIndex]

  return (
    <div className="book-reader">
      {/* Header */}
      <header className="reader-header">
        <button className="back-btn" onClick={() => navigate('/')}>
          <X size={24} />
        </button>
        <h1 className="reader-title">{decodeURIComponent(filename)}</h1>
        <div className="page-info">
          Page {currentPage} {totalPages > 0 && `of ${totalPages}`}
        </div>
      </header>

      {/* Main Content */}
      <div className="reader-content">
        {/* PDF Viewer */}
        <div className="pdf-viewer">
          <div className="pdf-container">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={
                <div className="pdf-loading">Loading PDF...</div>
              }
              error={
                <div className="pdf-error">Failed to load PDF</div>
              }
            >
              <Page
                pageNumber={currentPage}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                loading={<div className="page-loading">Loading page...</div>}
              />
            </Document>
          </div>
          
          {/* Page Navigation */}
          <div className="page-navigation">
            <button 
              className="nav-btn"
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft size={20} />
            </button>
            
            <form onSubmit={handlePageInputSubmit} className="page-input-form">
              <input
                type="text"
                className="page-input"
                value={pageInput}
                onChange={handlePageInputChange}
                onBlur={handlePageInputSubmit}
              />
              <span className="page-separator">/</span>
              <span className="page-total">{totalPages || '?'}</span>
            </form>
            
            <button 
              className="nav-btn"
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        {/* Quiz Panel */}
        <div className="quiz-panel">
          {!showQuiz ? (
            <div className="quiz-start">
              <div className="quiz-icon">
                <Brain size={48} />
              </div>
              <h2>Review Questions</h2>
              <p>Test your understanding of the material on this page</p>
              <button 
                className="start-quiz-btn"
                onClick={handleStartQuiz}
                disabled={loadingQuestions}
              >
                {loadingQuestions ? 'Loading...' : 'Start Quiz'}
              </button>
            </div>
          ) : (
            <div className="quiz-active">
              <div className="quiz-header">
                <span className="quiz-badge">Review Question</span>
                <span className="question-counter">
                  {currentQuestionIndex + 1} / {questions.length}
                </span>
              </div>

              {currentQuestion && (
                <>
                  <div className="question-tags">
                    <span className="tag">Recall</span>
                    <span className="tag">{currentQuestion.knowledge_name}</span>
                  </div>

                  <div className="question-text">
                    {currentQuestion.knowledge_question}
                  </div>

                  <textarea
                    className="answer-input"
                    placeholder="I've thought about it"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    rows={4}
                  />

                  <button 
                    className="hint-btn"
                    onClick={() => setShowHint(!showHint)}
                  >
                    <Lightbulb size={16} />
                    {showHint ? 'Hide hint' : 'Show hint'}
                  </button>

                  {showHint && (
                    <div className="hint-box">
                      Think about the key concepts covered on this page. Consider the definitions and examples provided.
                    </div>
                  )}

                  <div className="quiz-actions">
                    <button
                      className="nav-question-btn"
                      onClick={handlePreviousQuestion}
                      disabled={currentQuestionIndex === 0}
                    >
                      Previous
                    </button>
                    <button
                      className="nav-question-btn primary"
                      onClick={handleNextQuestion}
                    >
                      {currentQuestionIndex < questions.length - 1 ? 'Next' : 'Finish'}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default BookReader
