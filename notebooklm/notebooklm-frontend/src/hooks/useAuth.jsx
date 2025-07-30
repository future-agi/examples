import React, { createContext, useContext, useState, useEffect } from 'react'
import { useToast } from '@/hooks/use-toast'

const AuthContext = createContext()

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  // Check for existing token on app start
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      // Verify token with backend
      verifyToken(token)
    } else {
      setLoading(false)
    }
  }, [])

  const verifyToken = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setUser(data.data.user)
        } else {
          localStorage.removeItem('auth_token')
        }
      } else {
        localStorage.removeItem('auth_token')
      }
    } catch (error) {
      console.error('Token verification failed:', error)
      localStorage.removeItem('auth_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        const { user, access_token } = data.data
        localStorage.setItem('auth_token', access_token)
        setUser(user)
        
        toast({
          title: "Welcome back!",
          description: `Logged in as ${user.name}`,
        })
        
        return { success: true }
      } else {
        const errorMessage = data.error?.message || 'Login failed'
        toast({
          title: "Login Failed",
          description: errorMessage,
          variant: "destructive"
        })
        return { success: false, error: errorMessage }
      }
    } catch (error) {
      console.error('Login error:', error)
      const errorMessage = 'Network error. Please try again.'
      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive"
      })
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const register = async (name, email, password) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, password })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        const { user, access_token } = data.data
        localStorage.setItem('auth_token', access_token)
        setUser(user)
        
        toast({
          title: "Welcome to Openbook!",
          description: `Account created for ${user.name}`,
        })
        
        return { success: true }
      } else {
        const errorMessage = data.error?.message || 'Registration failed'
        toast({
          title: "Registration Failed",
          description: errorMessage,
          variant: "destructive"
        })
        return { success: false, error: errorMessage }
      }
    } catch (error) {
      console.error('Registration error:', error)
      const errorMessage = 'Network error. Please try again.'
      toast({
        title: "Registration Failed",
        description: errorMessage,
        variant: "destructive"
      })
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    toast({
      title: "Logged out",
      description: "You have been successfully logged out",
    })
  }

  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token')
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  const apiCall = async (endpoint, options = {}) => {
    const token = localStorage.getItem('auth_token')
    const isFormData = options.body instanceof FormData
    
    const defaultHeaders = {
      // Don't set Content-Type for FormData - browser sets it automatically with boundary
      ...(!isFormData && { 'Content-Type': 'application/json' }),
      ...getAuthHeaders(),
      ...options.headers
    }
    
    const defaultOptions = {
      headers: defaultHeaders
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...defaultOptions,
      ...options
    })

    // Handle unauthorized responses
    if (response.status === 401) {
      logout()
      throw new Error('Unauthorized')
    }

    return response
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    getAuthHeaders,
    apiCall
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

