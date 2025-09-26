import React, { useState, useRef } from 'react'
import { Upload, FileText, Brain, Clock, CheckCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

function Dashboard() {
  const [uploading, setUploading] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)
  const fileInputRef = useRef(null)

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
      
      toast.success(`File processed successfully! Found ${response.data.objects_count} objects.`)
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

  React.useEffect(() => {
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
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#28a745' }}>0</p>
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
      </div>
    </div>
  )
}

export default Dashboard
