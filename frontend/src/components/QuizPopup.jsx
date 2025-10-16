import React, { useState, useEffect } from 'react'
import { Brain, X, CheckCircle, XCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

// Custom Checkmark SVG
const CheckmarkIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 6L9 17l-5-5"/>
  </svg>
)

function QuizPopup({ isOpen, items = [], onClose, onComplete }) {
  const [pendingItems, setPendingItems] = useState(items)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const currentItem = pendingItems[currentQuestionIndex]
  const totalQuestions = pendingItems.length

  useEffect(() => {
    if (!isOpen) return
    setPendingItems(items || [])
    setCurrentQuestionIndex(0)
    setShowAnswer(false)
    setLoading(false)
  }, [isOpen, items])

  // Removed internal network fetch; items are provided by parent

  const handleAnswer = async (correct) => {
    if (!currentItem) return

    setSubmitting(true)
    try {
      await api.post('/quiz/answer', {
        node_id: currentItem.node_id,
        correct: correct,
        question_id: currentItem.question_id
      })
      
      toast.success(correct ? 'Correct! Well done!' : 'Incorrect. Keep learning!')
      
      // Move to next question or finish
      if (currentQuestionIndex < totalQuestions - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setShowAnswer(false) // Reset answer reveal for next question
      } else {
        // Quiz completed
        setCurrentQuestionIndex(0)
        setShowAnswer(false)
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
    setCurrentQuestionIndex(0)
    setPendingItems([])
    setShowAnswer(false)
    onClose()
  }

  const handleShowAnswer = () => {
    setShowAnswer(true)
  }

  const handleStartOver = () => {
    setCurrentQuestionIndex(0)
    setShowAnswer(false)
    // Reset to the initial items from props without network
    setPendingItems(items || [])
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-primary/10 via-accent/5 to-background flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-2xl shadow-2xl border border-border max-w-2xl w-full max-h-[80vh] overflow-auto animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <span className="text-muted">
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </span>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-muted rounded-full transition-smooth"
          >
            <X size={20} className="text-muted" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4">
          <div className="progress">
            <div 
              className="progress-bar"
              style={{ width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%` }}
            />
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="spinner mx-auto mb-4"></div>
              <p className="text-muted">Loading review items...</p>
            </div>
          ) : totalQuestions === 0 ? (
            <div className="text-center py-8">
              <Brain size={64} className="text-primary mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-4">No Reviews Available</h2>
              <p className="text-muted mb-6">
                You don't have any items ready for review right now.
              </p>
              <button onClick={handleClose} className="btn btn-primary">
                Close
              </button>
            </div>
          ) : (
            <>
              {/* Question Area */}
              <div className="mb-6">
                <h2 className="text-2xl font-semibold mb-4 leading-relaxed">
                  {currentItem.question}
                </h2>
                
                {/* Metadata Badges */}
                <div className="flex flex-wrap gap-2 mb-6">
                  <span className="badge">
                    <strong>Type:</strong> {currentItem.question_type}
                  </span>
                  <span className="badge">
                    <strong>Focus:</strong> {currentItem.cognitive_focus}
                  </span>
                </div>

                {/* Answer Flow */}
                {!showAnswer ? (
                  <div className="text-center">
                    <button
                      onClick={handleShowAnswer}
                      className="btn btn-outline px-8 py-3 text-lg transition-smooth"
                    >
                      Show Answer
                    </button>
                  </div>
                ) : (
                  <div className="animate-fade-in">
                    {/* Answer Section */}
                    <div className="bg-muted/50 rounded-xl p-6 mb-6">
                      <strong className="text-lg">Answer:</strong>
                      <p className="mt-2 text-muted leading-relaxed">
                        {currentItem.answer}
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4">
                      <button
                        onClick={() => handleAnswer(false)}
                        className="btn btn-destructive flex-1 flex items-center justify-center gap-2 py-3 text-lg transition-smooth"
                        disabled={submitting}
                      >
                        <XCircle size={20} />
                        I Don't Know
                      </button>
                      
                      <button
                        onClick={() => handleAnswer(true)}
                        className="btn btn-success-custom flex-1 flex items-center justify-center gap-2 py-3 text-lg transition-smooth"
                        disabled={submitting}
                      >
                        <CheckmarkIcon />
                        I Know This
                      </button>
                    </div>
                  </div>
                )}

                {submitting && (
                  <div className="text-center mt-6">
                    <div className="spinner mx-auto mb-2"></div>
                    <p className="text-muted">Processing your answer...</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default QuizPopup
