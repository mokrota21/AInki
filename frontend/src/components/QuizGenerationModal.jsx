import React, { useState, useEffect } from 'react'
import { X, Brain, DollarSign, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

function QuizGenerationModal({ isOpen, onClose, docId, docName, onSuccess }) {
  const [parameters, setParameters] = useState([])
  const [selectedParams, setSelectedParams] = useState({})
  const [loading, setLoading] = useState(false)
  const [priceEstimate, setPriceEstimate] = useState(null)
  const [showPriceConfirmation, setShowPriceConfirmation] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchParameters()
    }
  }, [isOpen])

  const fetchParameters = async () => {
    try {
      setLoading(true)
      const response = await api.post('/extract_objects_parameter')
      setParameters(response.data || [])
    } catch (error) {
      toast.error('Failed to load parameters: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleParameterChange = (paramName, value) => {
    setSelectedParams(prev => ({
      ...prev,
      [paramName]: value
    }))
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      const response = await api.post(`/price_approximation?doc_id=${docId}&prompt_key=${selectedParams.prompt_key || "general_textbook_prompt"}&model_name=${selectedParams.model_name || "gpt-5-nano"}`)
      setPriceEstimate(response.data)
      setShowPriceConfirmation(true)
    } catch (error) {
      toast.error('Failed to get price estimate: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmGeneration = async () => {
    try {
      setGenerating(true)
      const queryParams = new URLSearchParams({
        doc_id: docId,
        prompt_key: selectedParams.prompt_key || "general_textbook_prompt",
        kwargs: '', // FastAPI requires this parameter due to **kwargs in the function signature
        ...selectedParams
      })
      const response = await api.post(`/extract_objects?${queryParams}`)
      toast.success('Quiz generation started! This may take a few minutes.')
      onSuccess?.()
      onClose()
    } catch (error) {
      toast.error('Failed to start quiz generation: ' + (error.response?.data?.detail || error.message))
    } finally {
      setGenerating(false)
    }
  }

  const renderParameterInput = (param) => {
    switch (param.type) {
      case 'select':
        return (
          <select
            value={selectedParams[param.fetch_name] || ''}
            onChange={(e) => handleParameterChange(param.fetch_name, e.target.value)}
            className="form-input"
            required
          >
            <option value="">Select {param.name}</option>
            {param.values.map((option, index) => (
              <option key={index} value={option}>
                {option}
              </option>
            ))}
          </select>
        )
      
      case 'multiple_choice':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {param.values.map((option, index) => (
              <label key={index} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={selectedParams[param.fetch_name]?.includes(option) || false}
                  onChange={(e) => {
                    const currentValues = selectedParams[param.fetch_name] || []
                    if (e.target.checked) {
                      handleParameterChange(param.fetch_name, [...currentValues, option])
                    } else {
                      handleParameterChange(param.fetch_name, currentValues.filter(v => v !== option))
                    }
                  }}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        )
      
      case 'text':
        return (
          <input
            type="text"
            value={selectedParams[param.fetch_name] || ''}
            onChange={(e) => handleParameterChange(param.fetch_name, e.target.value)}
            className="form-input"
            placeholder={`Enter ${param.name}`}
            required
          />
        )
      
      default:
        return <div>Unsupported parameter type: {param.type}</div>
    }
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
        maxHeight: '90vh',
        overflow: 'auto',
        position: 'relative'
      }}>
        {/* Close button */}
        <button
          onClick={onClose}
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
          {showPriceConfirmation ? (
            /* Price Confirmation */
            <div>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <DollarSign size={48} style={{ color: '#28a745', marginBottom: '1rem' }} />
                <h2 style={{ marginBottom: '1rem', color: '#2c3e50' }}>Price Estimate</h2>
                <p style={{ color: '#6c757d', marginBottom: '1rem' }}>
                  Estimated cost for generating quizzes for "{docName}":
                </p>
                <div style={{ 
                  fontSize: '2rem', 
                  fontWeight: 'bold', 
                  color: '#28a745',
                  marginBottom: '1rem'
                }}>
                  ${priceEstimate?.price || '0.00'}
                </div>
                <div style={{ 
                  background: '#f8f9fa', 
                  padding: '1rem', 
                  borderRadius: '8px',
                  marginBottom: '2rem'
                }}>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#6c757d' }}>
                    This is an estimate based on document size and selected parameters.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button
                  onClick={() => setShowPriceConfirmation(false)}
                  className="btn btn-secondary"
                  disabled={generating}
                >
                  Back
                </button>
                <button
                  onClick={handleConfirmGeneration}
                  className="btn btn-primary"
                  disabled={generating}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {generating ? (
                    <>
                      <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <Brain size={16} />
                      Generate Quiz
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Parameter Selection */
            <div>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <Brain size={48} style={{ color: '#667eea', marginBottom: '1rem' }} />
                <h2 style={{ marginBottom: '1rem', color: '#2c3e50' }}>Generate Quiz</h2>
                <p style={{ color: '#6c757d' }}>
                  Configure parameters for quiz generation for "{docName}"
                </p>
              </div>

              {loading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
                  <p>Loading parameters...</p>
                </div>
              ) : (
                <div style={{ marginBottom: '2rem' }}>
                  {parameters.map((param, index) => (
                    <div key={index} className="form-group">
                      <label className="form-label">
                        {param.name}
                        {param.type === 'multiple_choice' && ' (Select all that apply)'}
                      </label>
                      {renderParameterInput(param)}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button
                  onClick={onClose}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  className="btn btn-primary"
                  disabled={loading || parameters.length === 0}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {loading ? (
                    <>
                      <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                      Calculating...
                    </>
                  ) : (
                    <>
                      <DollarSign size={16} />
                      Get Price Estimate
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default QuizGenerationModal
