import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { LogOut, BookOpen, Brain } from 'lucide-react'

function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="navbar">
      <div className="container">
        <div className="navbar-content">
          <Link to="/" className="logo">
            <Brain size={24} style={{ marginRight: '0.5rem' }} />
            AInki
          </Link>
          
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Link to="/dashboard" className="btn btn-secondary">
                <BookOpen size={16} style={{ marginRight: '0.5rem' }} />
                Dashboard
              </Link>
              <button onClick={logout} className="btn btn-secondary">
                <LogOut size={16} style={{ marginRight: '0.5rem' }} />
                Logout
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-secondary">Login</Link>
              <Link to="/register" className="btn btn-primary">Register</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
