import React, { createContext, useContext, useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from './useAuth'
import { useToast } from '@/hooks/use-toast'

const NotebookContext = createContext()

export function NotebookProvider({ children }) {
  const { notebookId } = useParams()
  const { apiCall } = useAuth()
  const { toast } = useToast()
  
  const [notebook, setNotebook] = useState(null)
  const [sources, setSources] = useState([])
  const [conversations, setConversations] = useState([])
  const [generatedContent, setGeneratedContent] = useState([])
  const [podcasts, setPodcasts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load notebook data
  useEffect(() => {
    if (notebookId) {
      loadNotebook()
      loadSources()
      loadConversations()
      loadGeneratedContent()
      loadPodcasts()
    }
  }, [notebookId])

  const loadNotebook = async () => {
    try {
      const response = await apiCall(`/notebooks/${notebookId}`)
      const data = await response.json()
      
      if (data.success) {
        setNotebook(data.data)
      } else {
        setError(data.error?.message || 'Failed to load notebook')
      }
    } catch (error) {
      console.error('Error loading notebook:', error)
      setError('Failed to load notebook')
    }
  }

  const loadSources = async () => {
    try {
      const response = await apiCall(`/notebooks/${notebookId}/sources`)
      const data = await response.json()
      
      if (data.success) {
        setSources(data.data.sources || [])
      }
    } catch (error) {
      console.error('Error loading sources:', error)
    }
  }

  const loadConversations = async () => {
    try {
      const response = await apiCall(`/chat/notebooks/${notebookId}/conversations`)
      const data = await response.json()
      
      if (data.success) {
        setConversations(data.data.conversations || [])
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    }
  }

  const loadGeneratedContent = async () => {
    try {
      const response = await apiCall(`/content/notebooks/${notebookId}/content`)
      const data = await response.json()
      
      if (data.success) {
        setGeneratedContent(data.data.content || [])
      }
    } catch (error) {
      console.error('Error loading generated content:', error)
    }
  }

  const loadPodcasts = async () => {
    try {
      const response = await apiCall(`/podcasts/notebooks/${notebookId}/podcasts`)
      const data = await response.json()
      
      if (data.success) {
        setPodcasts(data.data.podcasts || [])
      }
    } catch (error) {
      console.error('Error loading podcasts:', error)
    } finally {
      setLoading(false)
    }
  }

  const uploadSource = async (file, title, description) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (title) formData.append('title', title)
      if (description) formData.append('description', description)

      const response = await apiCall(`/notebooks/${notebookId}/sources`, {
        method: 'POST',
        body: formData
        // Don't set headers - let apiCall handle auth and Content-Type
      })

      const data = await response.json()

      if (data.success) {
        setSources(prev => [data.data, ...prev])
        toast({
          title: "Source uploaded",
          description: `${file.name} has been uploaded and is being processed`,
        })
        return { success: true, source: data.data }
      } else {
        toast({
          title: "Upload failed",
          description: data.error?.message || 'Failed to upload source',
          variant: "destructive"
        })
        return { success: false, error: data.error?.message }
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast({
        title: "Upload failed",
        description: 'Network error during upload',
        variant: "destructive"
      })
      return { success: false, error: 'Network error' }
    }
  }

  const deleteSource = async (sourceId) => {
    try {
      const response = await apiCall(`/notebooks/${notebookId}/sources/${sourceId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (data.success) {
        setSources(prev => prev.filter(s => s.id !== sourceId))
        toast({
          title: "Source deleted",
          description: "Source has been removed from the notebook",
        })
        return { success: true }
      } else {
        toast({
          title: "Delete failed",
          description: data.error?.message || 'Failed to delete source',
          variant: "destructive"
        })
        return { success: false }
      }
    } catch (error) {
      console.error('Delete error:', error)
      toast({
        title: "Delete failed",
        description: 'Network error during deletion',
        variant: "destructive"
      })
      return { success: false }
    }
  }

  const createConversation = async (title) => {
    try {
      const response = await apiCall(`/chat/notebooks/${notebookId}/conversations`, {
        method: 'POST',
        body: JSON.stringify({ title })
      })

      const data = await response.json()

      if (data.success) {
        setConversations(prev => [data.data, ...prev])
        return { success: true, conversation: data.data }
      } else {
        toast({
          title: "Failed to create conversation",
          description: data.error?.message || 'Unknown error',
          variant: "destructive"
        })
        return { success: false }
      }
    } catch (error) {
      console.error('Create conversation error:', error)
      return { success: false }
    }
  }

  const sendMessage = async (conversationId, message, stream = false) => {
    try {
      const response = await apiCall(`/chat/notebooks/${notebookId}/conversations/${conversationId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message, stream })
      })

      if (stream) {
        return response // Return response for streaming
      }

      const data = await response.json()

      if (data.success) {
        // Update conversation in state
        setConversations(prev => 
          prev.map(conv => 
            conv.id === conversationId 
              ? { ...conv, ...data.data.conversation }
              : conv
          )
        )
        return { success: true, data: data.data }
      } else {
        toast({
          title: "Failed to send message",
          description: data.error?.message || 'Unknown error',
          variant: "destructive"
        })
        return { success: false }
      }
    } catch (error) {
      console.error('Send message error:', error)
      return { success: false }
    }
  }

  const generateContent = async (type, title, customPrompt, sourceIds) => {
    try {
      const response = await apiCall(`/content/notebooks/${notebookId}/content/generate`, {
        method: 'POST',
        body: JSON.stringify({
          type,
          title,
          custom_prompt: customPrompt,
          source_ids: sourceIds
        })
      })

      const data = await response.json()

      if (data.success) {
        setGeneratedContent(prev => [data.data, ...prev])
        toast({
          title: "Content generated",
          description: `${type} has been generated successfully`,
        })
        return { success: true, content: data.data }
      } else {
        toast({
          title: "Generation failed",
          description: data.error?.message || 'Failed to generate content',
          variant: "destructive"
        })
        return { success: false }
      }
    } catch (error) {
      console.error('Generate content error:', error)
      toast({
        title: "Generation failed",
        description: 'Network error during generation',
        variant: "destructive"
      })
      return { success: false }
    }
  }

  const createPodcast = async (title, style, durationTarget, sourceIds, customInstructions, description) => {
    try {
      const response = await apiCall(`/podcasts/notebooks/${notebookId}/podcasts`, {
        method: 'POST',
        body: JSON.stringify({
          title,
          style,
          duration_target: durationTarget,
          source_ids: sourceIds,
          custom_instructions: customInstructions,
          description
        })
      })

      const data = await response.json()

      if (data.success) {
        setPodcasts(prev => [data.data, ...prev])
        toast({
          title: "Podcast generation started",
          description: "Your podcast is being generated. This may take a few minutes.",
        })
        return { success: true, podcast: data.data }
      } else {
        toast({
          title: "Podcast creation failed",
          description: data.error?.message || 'Failed to create podcast',
          variant: "destructive"
        })
        return { success: false }
      }
    } catch (error) {
      console.error('Create podcast error:', error)
      toast({
        title: "Podcast creation failed",
        description: 'Network error during creation',
        variant: "destructive"
      })
      return { success: false }
    }
  }

  const searchNotebook = async (query, maxResults = 20) => {
    try {
      const response = await apiCall(`/chat/notebooks/${notebookId}/search`, {
        method: 'POST',
        body: JSON.stringify({ query, max_results: maxResults })
      })

      const data = await response.json()

      if (data.success) {
        return { success: true, results: data.data.results }
      } else {
        return { success: false, error: data.error?.message }
      }
    } catch (error) {
      console.error('Search error:', error)
      return { success: false, error: 'Network error' }
    }
  }

  const refreshData = () => {
    loadSources()
    loadConversations()
    loadGeneratedContent()
    loadPodcasts()
  }

  const value = {
    notebook,
    sources,
    conversations,
    generatedContent,
    podcasts,
    loading,
    error,
    uploadSource,
    deleteSource,
    createConversation,
    sendMessage,
    generateContent,
    createPodcast,
    searchNotebook,
    refreshData
  }

  return (
    <NotebookContext.Provider value={value}>
      {children}
    </NotebookContext.Provider>
  )
}

export function useNotebook() {
  const context = useContext(NotebookContext)
  if (!context) {
    throw new Error('useNotebook must be used within a NotebookProvider')
  }
  return context
}

