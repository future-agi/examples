import React, { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useNotebook } from '@/hooks/useNotebook'
import { useToast } from '@/hooks/use-toast'
import { 
  Upload, 
  FileText, 
  File, 
  Trash2, 
  Download,
  Eye,
  AlertCircle,
  CheckCircle,
  Clock,
  Plus,
  X
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function SourcesTab() {
  const { sources, uploadSource, deleteSource } = useNotebook()
  const { toast } = useToast()
  const fileInputRef = useRef(null)
  
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploadForm, setUploadForm] = useState({ title: '', description: '' })
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const handleFileSelect = (file) => {
    setSelectedFile(file)
    setUploadForm(prev => ({ 
      ...prev, 
      title: prev.title || file.name.replace(/\.[^/.]+$/, '') 
    }))
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
      setUploadDialogOpen(true)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploading(true)
    try {
      const result = await uploadSource(
        selectedFile,
        uploadForm.title.trim(),
        uploadForm.description.trim()
      )

      if (result.success) {
        setUploadDialogOpen(false)
        setSelectedFile(null)
        setUploadForm({ title: '', description: '' })
      }
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (source) => {
    if (!confirm(`Are you sure you want to delete "${source.title}"? This action cannot be undone.`)) {
      return
    }

    await deleteSource(source.id)
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'processing':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Documents
          </CardTitle>
          <CardDescription>
            Add documents to your notebook. Supported formats: PDF, Word, Text, Audio, and more.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver 
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' 
                : 'border-gray-300 dark:border-gray-600'
            }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Drop files here or click to upload
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Supports PDF, DOCX, TXT, audio files, and other document formats
            </p>
            
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={() => fileInputRef.current?.click()}>
                  <Plus className="h-4 w-4 mr-2" />
                  Choose Files
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Upload Document</DialogTitle>
                  <DialogDescription>
                    Add a document to your notebook for AI analysis and chat.
                  </DialogDescription>
                </DialogHeader>
                
                <form onSubmit={handleUpload} className="space-y-4">
                  {!selectedFile ? (
                    <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                      <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Choose a file to upload
                      </p>
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => fileInputRef.current?.click()}
                      >
                        Select File
                      </Button>
                    </div>
                  ) : (
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="h-8 w-8 text-blue-600" />
                          <div>
                            <p className="font-medium">{selectedFile.name}</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {formatFileSize(selectedFile.size)}
                            </p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedFile(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <Label htmlFor="title">Title</Label>
                    <Input
                      id="title"
                      placeholder="Enter document title"
                      value={uploadForm.title}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description (optional)</Label>
                    <Textarea
                      id="description"
                      placeholder="Enter document description"
                      value={uploadForm.description}
                      onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                      rows={3}
                    />
                  </div>
                  
                  <div className="flex justify-end gap-2">
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setUploadDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={!selectedFile || uploading}>
                      {uploading ? <LoadingSpinner size="sm" /> : 'Upload'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.md,.rtf,.mp3,.wav,.m4a,.aac,.ogg,.flac,.mp4"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  handleFileSelect(file)
                  setUploadDialogOpen(true)
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Sources List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Documents ({sources.length})
          </h2>
        </div>

        {sources.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No documents yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Upload your first document to start using NotebookLM's AI features.
              </p>
              <Button onClick={() => setUploadDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Upload Document
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {sources.map((source) => (
              <Card key={source.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-gray-900 dark:text-white truncate">
                            {source.title}
                          </h3>
                          <Badge className={getStatusColor(source.status)}>
                            <div className="flex items-center gap-1">
                              {getStatusIcon(source.status)}
                              <span className="capitalize">{source.status}</span>
                            </div>
                          </Badge>
                        </div>
                        
                        {source.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {source.description}
                          </p>
                        )}
                        
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                          <span>Type: {source.type || 'Document'}</span>
                          {source.file_size && (
                            <span>Size: {formatFileSize(source.file_size)}</span>
                          )}
                          <span>Uploaded: {formatDate(source.created_at)}</span>
                        </div>
                        
                        {source.status === 'processing' && source.progress !== undefined && (
                          <div className="mt-3">
                            <div className="flex items-center justify-between text-sm mb-1">
                              <span>Processing...</span>
                              <span>{source.progress}%</span>
                            </div>
                            <Progress value={source.progress} className="h-2" />
                          </div>
                        )}
                        
                        {source.status === 'error' && source.error_message && (
                          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400">
                            Error: {source.error_message}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      <Button variant="ghost" size="sm" disabled={source.status !== 'processed'}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleDelete(source)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
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

