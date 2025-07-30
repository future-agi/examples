import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useNotebook } from '@/hooks/useNotebook'
import { 
  Mic, 
  Plus, 
  Play, 
  Download, 
  Users, 
  User, 
  BookOpen,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const podcastStyles = {
  conversational: {
    name: 'Conversational',
    description: 'Natural conversation between two hosts',
    icon: Users,
    voices: ['Host A (Female)', 'Host B (Male)']
  },
  interview: {
    name: 'Interview',
    description: 'Professional interview format',
    icon: User,
    voices: ['Interviewer (Female)', 'Expert (Male)']
  },
  narrative: {
    name: 'Narrative',
    description: 'Storytelling approach',
    icon: BookOpen,
    voices: ['Narrator (Male)']
  },
  educational: {
    name: 'Educational',
    description: 'Structured teaching format',
    icon: Clock,
    voices: ['Instructor (Female)']
  }
}

export default function PodcastsTab() {
  const { podcasts, createPodcast, sources } = useNotebook()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    style: 'conversational',
    durationTarget: 'medium',
    sourceIds: [],
    customInstructions: ''
  })
  const [creating, setCreating] = useState(false)

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!createForm.title.trim()) return

    setCreating(true)
    try {
      const result = await createPodcast(
        createForm.title.trim(),
        createForm.style,
        createForm.durationTarget,
        createForm.sourceIds.length > 0 ? createForm.sourceIds : undefined,
        createForm.customInstructions.trim() || undefined,
        createForm.description.trim() || undefined
      )

      if (result.success) {
        setCreateDialogOpen(false)
        setCreateForm({
          title: '',
          description: '',
          style: 'conversational',
          durationTarget: 'medium',
          sourceIds: [],
          customInstructions: ''
        })
      }
    } catch (error) {
      console.error('Create podcast error:', error)
    } finally {
      setCreating(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'generating':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'generating':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (minutes) => {
    if (minutes < 60) return `${Math.round(minutes)}m`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}m`
  }

  const processedSources = sources.filter(s => s.status === 'processed')

  return (
    <div className="space-y-6">
      {/* Create Podcast Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Create Audio Podcast
          </CardTitle>
          <CardDescription>
            Transform your documents into engaging audio podcasts with natural conversations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {Object.entries(podcastStyles).map(([style, config]) => {
              const Icon = config.icon
              return (
                <Card 
                  key={style}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => {
                    setCreateForm(prev => ({ ...prev, style }))
                    setCreateDialogOpen(true)
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <Icon className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                      </div>
                      <h3 className="font-medium">{config.name}</h3>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {config.description}
                    </p>
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      {config.voices.join(', ')}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <Button 
            onClick={() => setCreateDialogOpen(true)}
            disabled={processedSources.length === 0}
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Podcast
          </Button>

          {processedSources.length === 0 && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Upload and process documents first to create podcasts.
            </p>
          )}

          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Audio Podcast</DialogTitle>
                <DialogDescription>
                  Generate an engaging audio podcast from your documents.
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="podcast-title">Title</Label>
                  <Input
                    id="podcast-title"
                    placeholder="Enter podcast title"
                    value={createForm.title}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, title: e.target.value }))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="podcast-description">Description (optional)</Label>
                  <Textarea
                    id="podcast-description"
                    placeholder="Enter podcast description"
                    value={createForm.description}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="podcast-style">Style</Label>
                    <Select 
                      value={createForm.style} 
                      onValueChange={(value) => setCreateForm(prev => ({ ...prev, style: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(podcastStyles).map(([style, config]) => (
                          <SelectItem key={style} value={style}>
                            {config.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="duration-target">Duration</Label>
                    <Select 
                      value={createForm.durationTarget} 
                      onValueChange={(value) => setCreateForm(prev => ({ ...prev, durationTarget: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="short">Short (5-10 min)</SelectItem>
                        <SelectItem value="medium">Medium (15-20 min)</SelectItem>
                        <SelectItem value="long">Long (25-30 min)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Sources (optional)</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Leave empty to use all sources:
                  </p>
                  <div className="max-h-32 overflow-y-auto space-y-2">
                    {processedSources.map((source) => (
                      <label key={source.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={createForm.sourceIds.includes(source.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCreateForm(prev => ({
                                ...prev,
                                sourceIds: [...prev.sourceIds, source.id]
                              }))
                            } else {
                              setCreateForm(prev => ({
                                ...prev,
                                sourceIds: prev.sourceIds.filter(id => id !== source.id)
                              }))
                            }
                          }}
                          className="rounded"
                        />
                        <span className="text-sm">{source.title}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="custom-instructions">Custom Instructions (optional)</Label>
                  <Textarea
                    id="custom-instructions"
                    placeholder="Add specific instructions for the podcast..."
                    value={createForm.customInstructions}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, customInstructions: e.target.value }))}
                    rows={3}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setCreateDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={creating}>
                    {creating ? <LoadingSpinner size="sm" /> : 'Create Podcast'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Podcasts List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Podcasts ({podcasts.length})
          </h2>
        </div>

        {podcasts.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Mic className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No podcasts yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Create your first audio podcast from your documents.
              </p>
              <Button 
                onClick={() => setCreateDialogOpen(true)}
                disabled={processedSources.length === 0}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Podcast
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {podcasts.map((podcast) => {
              const styleConfig = podcastStyles[podcast.style] || podcastStyles.conversational
              const Icon = styleConfig.icon
              
              return (
                <Card key={podcast.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4 flex-1">
                        <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                          <Icon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-gray-900 dark:text-white truncate">
                              {podcast.title}
                            </h3>
                            <Badge className={getStatusColor(podcast.status)}>
                              <div className="flex items-center gap-1">
                                {getStatusIcon(podcast.status)}
                                <span className="capitalize">{podcast.status}</span>
                              </div>
                            </Badge>
                          </div>
                          
                          {podcast.description && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                              {podcast.description}
                            </p>
                          )}
                          
                          <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500 mb-2">
                            <span>Style: {styleConfig.name}</span>
                            {podcast.estimated_duration && (
                              <span>Duration: {formatDuration(podcast.estimated_duration)}</span>
                            )}
                            <span>Created: {formatDate(podcast.created_at)}</span>
                          </div>
                          
                          {podcast.status === 'generating' && podcast.progress !== undefined && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between text-sm mb-1">
                                <span>Generating podcast...</span>
                                <span>{podcast.progress}%</span>
                              </div>
                              <Progress value={podcast.progress} className="h-2" />
                            </div>
                          )}
                          
                          {podcast.status === 'error' && podcast.error_message && (
                            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400">
                              Error: {podcast.error_message}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {podcast.status === 'completed' && (
                        <div className="flex items-center gap-2 ml-4">
                          <Button variant="ghost" size="sm">
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

