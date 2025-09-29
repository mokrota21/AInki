import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('token')
    if (token) {
      setUser({ userid: token })
    }
    setLoading(false)
  }, [])

  const login = async (usernameOrGmail, password) => {
    try {
      const response = await api.post('auth/login', {
        username_or_gmail: usernameOrGmail,
        password: password
      })
      
      const { userid } = response.data
      localStorage.setItem('token', userid)
      setUser({ userid })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const register = async (username, password, gmail) => {
    try {
      const response = await api.post('auth/register', {
        username,
        password,
        gmail
      })
      
      const { userid } = response.data
      localStorage.setItem('token', userid)
      setUser({ userid })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Registration failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  const value = {
    user,
    login,
    register,
    logout,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
