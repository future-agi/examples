import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { useNotebook } from '@/hooks/useNotebook'
import { 
  BookOpen, 
  Plus, 
  FileText, 
  HelpCircle, 
  Clock, 
  GraduationCap,
  ClipboardList,
  Sparkles
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const contentTypes = {
  summary: {
    name: 'Summary',
    description: 'Create a comprehensive summary of your documents',
    icon: FileText,
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
  },
  faq: {
    name: 'FAQ',
    description: 'Generate frequently asked questions and answers',
    icon: HelpCircle,
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
  },
  timeline: {
    name: 'Timeline',
    description: 'Create a chronological timeline of events',
    icon: Clock,
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
  },
  study_guide: {
    name: 'Study Guide',
    description: 'Generate a comprehensive study guide',
    icon: GraduationCap,
    color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300'
  },
  briefing: {
    name: 'Briefing',
    description: 'Create a concise briefing document',
    icon: ClipboardList,
    color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300'
  }
}

export default function ContentTab() {
  const { generatedContent, generateContent, sources } = useNotebook()
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false)
  const [generateForm, setGenerateForm] = useState({
    type: '',
    title: '',
    customPrompt: '',
    sourceIds: []
  })
  const [generating, setGenerating] = useState(false)
  const [expandedContent, setExpandedContent] = useState(new Set())

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!generateForm.type) return

    setGenerating(true)
    try {
      const result = await generateContent(
        generateForm.type,
        generateForm.title.trim() || undefined,
        generateForm.customPrompt.trim() || undefined,
        generateForm.sourceIds.length > 0 ? generateForm.sourceIds : undefined
      )

      if (result.success) {
        setGenerateDialogOpen(false)
        setGenerateForm({ type: '', title: '', customPrompt: '', sourceIds: [] })
      }
    } catch (error) {
      console.error('Generate error:', error)
    } finally {
      setGenerating(false)
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

  const toggleContentExpansion = (contentId) => {
    setExpandedContent(prev => {
      const newSet = new Set(prev)
      if (newSet.has(contentId)) {
        newSet.delete(contentId)
      } else {
        newSet.add(contentId)
      }
      return newSet
    })
  }

  const processedSources = sources.filter(s => s.status === 'processed')

  return (
    <div className="space-y-6">
      {/* Generate Content Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Generate Content
          </CardTitle>
          <CardDescription>
            Create summaries, FAQs, study guides, and more from your documents using AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(contentTypes).map(([type, config]) => {
              const Icon = config.icon
              return (
                <Card 
                  key={type}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => {
                    setGenerateForm(prev => ({ ...prev, type }))
                    setGenerateDialogOpen(true)
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-2 rounded-lg ${config.color}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <h3 className="font-medium">{config.name}</h3>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {config.description}
                    </p>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>
                  Generate {generateForm.type ? contentTypes[generateForm.type]?.name : 'Content'}
                </DialogTitle>
                <DialogDescription>
                  {generateForm.type ? contentTypes[generateForm.type]?.description : 'Select content type and customize generation options.'}
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="content-type">Content Type</Label>
                  <Select 
                    value={generateForm.type} 
                    onValueChange={(value) => setGenerateForm(prev => ({ ...prev, type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select content type" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(contentTypes).map(([type, config]) => (
                        <SelectItem key={type} value={type}>
                          <div className="flex items-center gap-2">
                            <config.icon className="h-4 w-4" />
                            {config.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">Title (optional)</Label>
                  <Input
                    id="title"
                    placeholder="Enter custom title"
                    value={generateForm.title}
                    onChange={(e) => setGenerateForm(prev => ({ ...prev, title: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="custom-prompt">Custom Instructions (optional)</Label>
                  <Textarea
                    id="custom-prompt"
                    placeholder="Add specific instructions for content generation..."
                    value={generateForm.customPrompt}
                    onChange={(e) => setGenerateForm(prev => ({ ...prev, customPrompt: e.target.value }))}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Sources (optional)</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Leave empty to use all sources, or select specific documents:
                  </p>
                  <div className="max-h-32 overflow-y-auto space-y-2">
                    {processedSources.map((source) => (
                      <label key={source.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={generateForm.sourceIds.includes(source.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setGenerateForm(prev => ({
                                ...prev,
                                sourceIds: [...prev.sourceIds, source.id]
                              }))
                            } else {
                              setGenerateForm(prev => ({
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

                <div className="flex justify-end gap-2">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setGenerateDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    disabled={!generateForm.type || generating || processedSources.length === 0}
                  >
                    {generating ? <LoadingSpinner size="sm" /> : 'Generate'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Generated Content List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Generated Content ({generatedContent.length})
          </h2>
        </div>

        {generatedContent.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No generated content yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Generate summaries, FAQs, study guides, and more from your documents.
              </p>
              <Button onClick={() => setGenerateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Generate Content
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {generatedContent.map((content) => {
              const typeConfig = contentTypes[content.type] || contentTypes.summary
              const Icon = typeConfig.icon
              const isExpanded = expandedContent.has(content.id)
              const shouldTruncate = content.content.length > 500
              
              return (
                <Card key={content.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${typeConfig.color}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{content.title}</CardTitle>
                          <CardDescription>
                            {typeConfig.name} • Generated {formatDate(content.created_at)}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {content.word_count || 0} words
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="prose dark:prose-invert max-w-none">
                      <div className="whitespace-pre-wrap text-sm">
                        {shouldTruncate && !isExpanded 
                          ? content.content.substring(0, 500) + '...'
                          : content.content
                        }
                      </div>
                    </div>
                    {shouldTruncate && (
                      <Button 
                        variant="link" 
                        className="p-0 h-auto mt-2"
                        onClick={() => toggleContentExpansion(content.id)}
                      >
                        {isExpanded ? 'Read less' : 'Read more'}
                      </Button>
                    )}
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

