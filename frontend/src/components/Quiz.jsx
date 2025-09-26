import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Brain, CheckCircle, XCircle, RotateCcw } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

function Quiz() {
  const [pendingItems, setPendingItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const currentItem = pendingItems[currentIndex]

  useEffect(() => {
    loadPendingItems()
  }, [])

  const loadPendingItems = async () => {
    try {
      const response = await api.get('/pending')
      setPendingItems(response.data)
      setLoading(false)
    } catch (error) {
      toast.error('Failed to load pending items')
      setLoading(false)
    }
  }

  const handleAnswer = async (correct) => {
    if (!currentItem) return

    setSubmitting(true)
    try {
      await api.post('/quiz/answer', {
        node_id: currentItem.node_id,
        correct: correct
      })
      
      toast.success(correct ? 'Correct! Well done!' : 'Incorrect. Keep learning!')
      
      // Move to next item or finish
      if (currentIndex < pendingItems.length - 1) {
        setCurrentIndex(currentIndex + 1)
      } else {
        toast.success('Review session completed!')
        navigate('/dashboard')
      }
    } catch (error) {
      toast.error('Failed to submit answer')
    } finally {
      setSubmitting(false)
    }
  }

  const resetSession = () => {
    setCurrentIndex(0)
    loadPendingItems()
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading review items...</p>
      </div>
    )
  }

  if (pendingItems.length === 0) {
    return (
      <div className="container">
        <div className="quiz-card">
          <Brain size={64} style={{ color: '#667eea', marginBottom: '1rem' }} />
          <h1 className="quiz-title">No Reviews Available</h1>
          <p className="quiz-content">
            You don't have any items ready for review right now. 
            Upload some documents and come back later!
          </p>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="quiz-card">
        {/* Progress */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ color: '#6c757d' }}>
              Question {currentIndex + 1} of {pendingItems.length}
            </span>
            <button onClick={resetSession} className="btn btn-secondary" style={{ padding: '0.5rem' }}>
              <RotateCcw size={16} />
            </button>
          </div>
          <div style={{ 
            width: '100%', 
            height: '8px', 
            background: '#e9ecef', 
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${((currentIndex + 1) / pendingItems.length) * 100}%`,
              height: '100%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              transition: 'width 0.3s ease'
            }}></div>
          </div>
        </div>

        {/* Question */}
        <h1 className="quiz-title">{currentItem.name}</h1>
        <div className="quiz-content">
          <p>{currentItem.content}</p>
          <div style={{ 
            marginTop: '1rem', 
            padding: '1rem', 
            background: '#f8f9fa', 
            borderRadius: '8px',
            fontSize: '0.9rem',
            color: '#6c757d'
          }}>
            <strong>Source:</strong> Document {currentItem.doc_id}, Chunks {currentItem.chunk_start}-{currentItem.chunk_end}
          </div>
        </div>

        {/* Answer Buttons */}
        <div className="quiz-actions">
          <button
            onClick={() => handleAnswer(false)}
            className="btn btn-danger"
            disabled={submitting}
            style={{ padding: '1rem 2rem', fontSize: '1.1rem' }}
          >
            <XCircle size={20} style={{ marginRight: '0.5rem' }} />
            I Don't Know
          </button>
          
          <button
            onClick={() => handleAnswer(true)}
            className="btn btn-success"
            disabled={submitting}
            style={{ padding: '1rem 2rem', fontSize: '1.1rem' }}
          >
            <CheckCircle size={20} style={{ marginRight: '0.5rem' }} />
            I Know This
          </button>
        </div>

        {submitting && (
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <div className="spinner" style={{ margin: '0 auto' }}></div>
            <p>Processing your answer...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Quiz
