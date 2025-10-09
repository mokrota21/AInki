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
  const [answerRevealed, setAnswerRevealed] = useState(false)
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
        setAnswerRevealed(false) // Reset answer reveal for next question
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

  const toggleAnswer = () => {
    setAnswerRevealed(!answerRevealed)
  }

  const resetSession = () => {
    setCurrentIndex(0)
    setAnswerRevealed(false)
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
        <div className="quiz-content">
          <h1 className="quiz-title">{currentItem.question}</h1>
          
          {/* Question metadata */}
          <div style={{ 
            marginBottom: '1.5rem', 
            padding: '0.75rem', 
            background: '#f8f9fa', 
            borderRadius: '8px',
            fontSize: '0.9rem',
            color: '#6c757d',
            display: 'flex',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <span><strong>Type:</strong> {currentItem.question_type}</span>
            <span><strong>Difficulty:</strong> {currentItem.difficulty}</span>
            <span><strong>Focus:</strong> {currentItem.cognitive_focus}</span>
          </div>

          {/* Answer section */}
          {answerRevealed && (
            <div style={{ 
              marginTop: '1rem', 
              padding: '1rem', 
              background: '#e9ecef', 
              borderRadius: '8px',
              fontSize: '0.9rem',
              color: '#495057'
            }}>
              <strong>Answer:</strong> {currentItem.content}
            </div>
          )}
        </div>

        {/* Show Answer Button */}
        {!answerRevealed && (
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <button
              onClick={toggleAnswer}
              className="btn btn-secondary"
              style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}
            >
              Show Answer
            </button>
          </div>
        )}

        {/* Answer Buttons - only show when answer is revealed */}
        {answerRevealed && (
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
        )}

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
