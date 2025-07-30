import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/use-toast'
import { 
  Plus, 
  BookOpen, 
  FileText, 
  MessageSquare, 
  Mic, 
  Search,
  Settings,
  LogOut,
  Brain,
  Calendar,
  Users,
  TrendingUp
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, logout, apiCall } = useAuth()
  const { toast } = useToast()
  
  const [notebooks, setNotebooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newNotebook, setNewNotebook] = useState({ title: '', description: '' })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadNotebooks()
  }, [])

  const loadNotebooks = async () => {
    try {
      const response = await apiCall('/notebooks')
      const data = await response.json()
      
      if (data.success) {
        setNotebooks(data.data.notebooks || [])
      } else {
        toast({
          title: "Failed to load notebooks",
          description: data.error?.message || 'Unknown error',
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error loading notebooks:', error)
      toast({
        title: "Failed to load notebooks",
        description: 'Network error',
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const createNotebook = async (e) => {
    e.preventDefault()
    if (!newNotebook.title.trim()) return

    setCreating(true)
    try {
      const response = await apiCall('/notebooks', {
        method: 'POST',
        body: JSON.stringify({
          title: newNotebook.title.trim(),
          description: newNotebook.description.trim()
        })
      })

      const data = await response.json()

      if (data.success) {
        setNotebooks(prev => [data.data, ...prev])
        setCreateDialogOpen(false)
        setNewNotebook({ title: '', description: '' })
        toast({
          title: "Notebook created",
          description: `"${data.data.title}" has been created successfully`,
        })
      } else {
        toast({
          title: "Failed to create notebook",
          description: data.error?.message || 'Unknown error',
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error creating notebook:', error)
      toast({
        title: "Failed to create notebook",
        description: 'Network error',
        variant: "destructive"
      })
    } finally {
      setCreating(false)
    }
  }

  const deleteNotebook = async (notebookId, title) => {
    if (!confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
      return
    }

    try {
      const response = await apiCall(`/notebooks/${notebookId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (data.success) {
        setNotebooks(prev => prev.filter(n => n.id !== notebookId))
        toast({
          title: "Notebook deleted",
          description: `"${title}" has been deleted`,
        })
      } else {
        toast({
          title: "Failed to delete notebook",
          description: data.error?.message || 'Unknown error',
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error deleting notebook:', error)
      toast({
        title: "Failed to delete notebook",
        description: 'Network error',
        variant: "destructive"
      })
    }
  }

  const filteredNotebooks = notebooks.filter(notebook =>
    notebook.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    notebook.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'archived': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
      default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Openbook
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 dark:text-gray-300">
                Welcome, {user?.name}
              </span>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Notebooks
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {notebooks.length}
                  </p>
                </div>
                <BookOpen className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Sources
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {notebooks.reduce((sum, nb) => sum + (nb.sources_count || 0), 0)}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Conversations
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {notebooks.reduce((sum, nb) => sum + (nb.conversations_count || 0), 0)}
                  </p>
                </div>
                <MessageSquare className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Podcasts
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {notebooks.reduce((sum, nb) => sum + (nb.podcasts_count || 0), 0)}
                  </p>
                </div>
                <Mic className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Create */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search notebooks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Notebook
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Notebook</DialogTitle>
                <DialogDescription>
                  Create a new notebook to organize your documents and research.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={createNotebook} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    placeholder="Enter notebook title"
                    value={newNotebook.title}
                    onChange={(e) => setNewNotebook(prev => ({ ...prev, title: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Enter notebook description"
                    value={newNotebook.description}
                    onChange={(e) => setNewNotebook(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={creating}>
                    {creating ? <LoadingSpinner size="sm" /> : 'Create Notebook'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Notebooks Grid */}
        {filteredNotebooks.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {searchQuery ? 'No notebooks found' : 'No notebooks yet'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchQuery 
                ? 'Try adjusting your search terms'
                : 'Create your first notebook to get started with Openbook'
              }
            </p>
            {!searchQuery && (
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Notebook
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredNotebooks.map((notebook) => (
              <Card 
                key={notebook.id} 
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(`/notebook/${notebook.id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-1">{notebook.title}</CardTitle>
                      <CardDescription className="line-clamp-2">
                        {notebook.description || 'No description'}
                      </CardDescription>
                    </div>
                    <Badge className={getStatusColor(notebook.status)}>
                      {notebook.status || 'active'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <FileText className="h-4 w-4" />
                        <span>{notebook.sources_count || 0} sources</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MessageSquare className="h-4 w-4" />
                        <span>{notebook.conversations_count || 0} chats</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Mic className="h-4 w-4" />
                        <span>{notebook.podcasts_count || 0} podcasts</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>Created {formatDate(notebook.created_at)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        <span>Updated {formatDate(notebook.updated_at)}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

