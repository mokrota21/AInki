import React, { useState, useRef } from 'react'
import { Upload, FileText, Brain, Clock, CheckCircle, Plus, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import QuizGenerationModal from './QuizGenerationModal'

function Dashboard() {
  const [uploading, setUploading] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)
  const [docs, setDocs] = useState([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [quizModalOpen, setQuizModalOpen] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

  const handleFileUpload = async (file) => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      const chunksCount = response?.data?.chunks_count
      toast.success(
        chunksCount != null
          ? `File processed successfully! Split into ${chunksCount} chunks.`
          : 'File processed successfully!'
      )
      fetchDocs()
      checkPendingItems()
    } catch (error) {
      toast.error('Upload failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const checkPendingItems = async () => {
    try {
      const response = await api.get('/pending')
      setPendingCount(response.data.length)
    } catch (error) {
      console.error('Failed to check pending items:', error)
    }
  }

  const fetchDocs = async () => {
    try {
      setDocsLoading(true)
      const response = await api.get('/docs')
      const docsData = response.data?.docs || []
      const globalHasQuiz = response.data?.has_quiz ?? false
      
      const normalized = docsData.map((d) => {
        if (d && typeof d === 'object' && !Array.isArray(d)) {
          return { 
            id: d.id ?? d.doc_id ?? null, 
            name: d.name ?? 'Unnamed',
            has_quiz: globalHasQuiz, // Use global has_quiz for all docs
            status: globalHasQuiz ? 'ready' : 'no_quiz'
          }
        }
        if (Array.isArray(d)) {
          return { 
            id: d[0] ?? null, 
            name: d[1] ?? 'Unnamed',
            has_quiz: globalHasQuiz, // Use global has_quiz for all docs
            status: globalHasQuiz ? 'ready' : 'no_quiz'
          }
        }
        return { 
          id: null, 
          name: String(d),
          has_quiz: globalHasQuiz, // Use global has_quiz for all docs
          status: globalHasQuiz ? 'ready' : 'no_quiz'
        }
      })
      setDocs(normalized)
    } catch (error) {
      console.error('Failed to fetch docs:', error)
    } finally {
      setDocsLoading(false)
    }
  }

  const handleOpenDoc = (doc) => {
    if (!doc?.id) return
    navigate(`/docs/${doc.id}`)
  }

  const handleGenerateQuiz = (doc, e) => {
    e.stopPropagation() // Prevent opening the document
    setSelectedDoc(doc)
    setQuizModalOpen(true)
  }

  const handleQuizGenerationSuccess = () => {
    fetchDocs() // Refresh the docs list to update status
    checkPendingItems() // Refresh pending count
  }

  const getStatusColor = (doc) => {
    if (doc.has_quiz) return '#28a745' // Green for has quiz
    if (doc.status === 'processing') return '#ffc107' // Yellow for processing
    if (doc.status === 'error') return '#dc3545' // Red for error
    return '#6c757d' // Gray for no quiz
  }

  const getStatusIcon = (doc) => {
    if (doc.has_quiz) return <CheckCircle size={16} />
    if (doc.status === 'processing') return <Clock size={16} />
    if (doc.status === 'error') return <AlertCircle size={16} />
    return null
  }

  const getStatusText = (doc) => {
    if (doc.has_quiz) return 'Quiz Ready'
    if (doc.status === 'processing') return 'Generating Quiz...'
    if (doc.status === 'error') return 'Generation Failed'
    return 'No Quiz'
  }

  React.useEffect(() => {
    fetchDocs()
    checkPendingItems()
    const interval = setInterval(checkPendingItems, 60000) // Check every minute
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="container">
      <div style={{ marginTop: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', textAlign: 'center' }}>
          Welcome to AInki
        </h1>
        <p style={{ textAlign: 'center', color: '#6c757d', marginBottom: '3rem' }}>
          Upload your documents and start learning through spaced repetition
        </p>

        {/* Upload Section */}
        <div className="card">
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={24} />
            Upload Document
          </h2>
          
          <div
            className={`upload-area ${uploading ? 'uploading' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            style={{ cursor: uploading ? 'not-allowed' : 'pointer' }}
          >
            {uploading ? (
              <div>
                <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
                <p>Processing your document...</p>
              </div>
            ) : (
              <div>
                <Upload size={48} style={{ color: '#667eea', marginBottom: '1rem' }} />
                <h3>Drop your file here or click to browse</h3>
                <p style={{ color: '#6c757d', marginTop: '0.5rem' }}>
                  Supported formats: PDF, TXT, DOCX
                </p>
              </div>
            )}
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            accept=".pdf,.txt,.docx"
            disabled={uploading}
          />
        </div>

        {/* Stats Section */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '2rem' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <FileText size={32} style={{ color: '#28a745', marginBottom: '1rem' }} />
            <h3>Documents Processed</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#28a745' }}>{docs.length}</p>
          </div>
          
          <div className="card" style={{ textAlign: 'center' }}>
            <Brain size={32} style={{ color: '#667eea', marginBottom: '1rem' }} />
            <h3>Knowledge Objects</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#667eea' }}>0</p>
          </div>
          
          <div className="card" style={{ textAlign: 'center' }}>
            <Clock size={32} style={{ color: '#ffc107', marginBottom: '1rem' }} />
            <h3>Pending Reviews</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ffc107' }}>{pendingCount}</p>
          </div>
          
          <div className="card" style={{ textAlign: 'center' }}>
            <CheckCircle size={32} style={{ color: '#17a2b8', marginBottom: '1rem' }} />
            <h3>Completed Reviews</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#17a2b8' }}>0</p>
          </div>
        </div>

        {/* Docs Gallery */}
        <div className="card" style={{ marginTop: '2rem' }}>
          <h2 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={24} />
            Your Documents
          </h2>
          {docsLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem' }}>
              <div className="spinner"></div>
            </div>
          ) : docs.length === 0 ? (
            <p style={{ color: '#6c757d' }}>No documents yet. Upload one to get started.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              {docs.map((doc, index) => (
                <div
                  key={doc.id != null ? `doc-${doc.id}` : `doc-${doc.name}-${index}`}
                  className="card"
                  style={{ 
                    padding: '1rem', 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.75rem', 
                    cursor: 'pointer',
                    position: 'relative',
                    border: `2px solid ${getStatusColor(doc)}`,
                    borderRadius: '12px'
                  }}
                  onClick={() => handleOpenDoc(doc)}
                >
                  <FileText size={20} style={{ color: '#667eea' }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis', 
                      whiteSpace: 'nowrap',
                      fontWeight: '500',
                      marginBottom: '0.25rem'
                    }}>
                      {doc.name}
                    </div>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem',
                      fontSize: '0.875rem',
                      color: getStatusColor(doc)
                    }}>
                      {getStatusIcon(doc)}
                      <span>{getStatusText(doc)}</span>
                    </div>
                  </div>
                  
                  {/* Quiz Generation Button */}
                  <button
                    onClick={(e) => handleGenerateQuiz(doc, e)}
                    className="btn btn-primary"
                    style={{ 
                      padding: '0.5rem',
                      fontSize: '0.875rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      minWidth: 'auto'
                    }}
                    title="Generate Quiz"
                  >
                    <Plus size={16} />
                    Quiz
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Document Viewer removed; handled on dedicated page */}

        {/* Quick Actions */}
        {pendingCount > 0 && (
          <div className="card" style={{ marginTop: '2rem', textAlign: 'center' }}>
            <h2 style={{ marginBottom: '1rem' }}>Ready to Review?</h2>
            <p style={{ color: '#6c757d', marginBottom: '1.5rem' }}>
              You have {pendingCount} items ready for review
            </p>
            <a href="/quiz" className="btn btn-primary" style={{ fontSize: '1.1rem', padding: '1rem 2rem' }}>
              Start Review Session
            </a>
          </div>
        )}

        {/* Quiz Generation Modal */}
        <QuizGenerationModal
          isOpen={quizModalOpen}
          onClose={() => setQuizModalOpen(false)}
          docId={selectedDoc?.id}
          docName={selectedDoc?.name}
          onSuccess={handleQuizGenerationSuccess}
        />
      </div>
    </div>
  )
}

export default Dashboard
