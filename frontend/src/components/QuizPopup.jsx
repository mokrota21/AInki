import React, { useState, useEffect } from 'react'
import { Brain, CheckCircle, XCircle, X } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

function QuizPopup({ isOpen, onClose, onComplete }) {
  const [pendingItems, setPendingItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [answerRevealed, setAnswerRevealed] = useState(false)

  const currentItem = pendingItems[currentIndex]

  useEffect(() => {
    if (isOpen) {
      loadPendingItems()
    }
  }, [isOpen])

  const loadPendingItems = async () => {
    try {
      setLoading(true)
      const response = await api.get('/pending')
      setPendingItems(response.data)
    } catch (error) {
      toast.error('Failed to load pending items')
    } finally {
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
        onComplete?.()
        onClose()
      }
    } catch (error) {
      toast.error('Failed to submit answer')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setCurrentIndex(0)
    setPendingItems([])
    setAnswerRevealed(false)
    onClose()
  }

  const toggleAnswer = () => {
    setAnswerRevealed(!answerRevealed)
  }

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '1rem'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
        maxWidth: '600px',
        width: '100%',
        maxHeight: '80vh',
        overflow: 'auto',
        position: 'relative'
      }}>
        {/* Close button */}
        <button
          onClick={handleClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.5rem',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1
          }}
        >
          <X size={20} color="#6c757d" />
        </button>

        <div style={{ padding: '2rem' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
              <p>Loading review items...</p>
            </div>
          ) : pendingItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <Brain size={64} style={{ color: '#667eea', marginBottom: '1rem' }} />
              <h2 style={{ marginBottom: '1rem', color: '#2c3e50' }}>No Reviews Available</h2>
              <p style={{ color: '#6c757d', marginBottom: '2rem' }}>
                You don't have any items ready for review right now.
              </p>
              <button onClick={handleClose} className="btn btn-primary">
                Close
              </button>
            </div>
          ) : (
            <>
              {/* Progress */}
              <div style={{ marginBottom: '2rem' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  marginBottom: '1rem' 
                }}>
                  <span style={{ color: '#6c757d' }}>
                    Question {currentIndex + 1} of {pendingItems.length}
                  </span>
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
              <h2 style={{ 
                marginBottom: '1.5rem', 
                color: '#2c3e50',
                fontSize: '1.5rem',
                fontWeight: '600'
              }}>
                {currentItem.question}
              </h2>
              
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
                  marginBottom: '2rem', 
                  padding: '1rem', 
                  background: '#e9ecef', 
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  color: '#495057'
                }}>
                  <strong>Answer:</strong> {currentItem.content}
                </div>
              )}

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
                <div style={{ 
                  display: 'flex', 
                  gap: '1rem', 
                  justifyContent: 'center',
                  flexWrap: 'wrap'
                }}>
                  <button
                    onClick={() => handleAnswer(false)}
                    className="btn btn-danger"
                    disabled={submitting}
                    style={{ 
                      padding: '1rem 2rem', 
                      fontSize: '1rem',
                      minWidth: '140px'
                    }}
                  >
                    <XCircle size={18} style={{ marginRight: '0.5rem' }} />
                    I Don't Know
                  </button>
                  
                  <button
                    onClick={() => handleAnswer(true)}
                    className="btn btn-success"
                    disabled={submitting}
                    style={{ 
                      padding: '1rem 2rem', 
                      fontSize: '1rem',
                      minWidth: '140px'
                    }}
                  >
                    <CheckCircle size={18} style={{ marginRight: '0.5rem' }} />
                    I Know This
                  </button>
                </div>
              )}

              {submitting && (
                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <div className="spinner" style={{ margin: '0 auto' }}></div>
                  <p style={{ marginTop: '0.5rem', color: '#6c757d' }}>Processing your answer...</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default QuizPopup
