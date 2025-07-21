import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useNotebook } from '@/hooks/useNotebook'
import { useAuth } from '@/hooks/useAuth'
import { 
  ArrowLeft, 
  FileText, 
  MessageSquare, 
  Mic, 
  BookOpen,
  Settings,
  Search,
  Plus,
  Brain
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

// Import notebook components
import SourcesTab from './SourcesTab'
import ChatTab from './ChatTab'
import ContentTab from './ContentTab'
import PodcastsTab from './PodcastsTab'
import SearchTab from './SearchTab'

export default function NotebookView() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { notebook, loading, error } = useNotebook()
  const [activeTab, setActiveTab] = useState('sources')

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Error Loading Notebook
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Button onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  if (!notebook) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Notebook Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            The notebook you're looking for doesn't exist or you don't have access to it.
          </p>
          <Button onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate('/dashboard')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
              
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <Brain className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {notebook.title}
                  </h1>
                  {notebook.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {notebook.description}
                    </p>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-300">
                {user?.name}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="sources" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Sources</span>
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">Chat</span>
            </TabsTrigger>
            <TabsTrigger value="content" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Content</span>
            </TabsTrigger>
            <TabsTrigger value="podcasts" className="flex items-center gap-2">
              <Mic className="h-4 w-4" />
              <span className="hidden sm:inline">Podcasts</span>
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Search</span>
            </TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="sources" className="space-y-4">
              <SourcesTab />
            </TabsContent>

            <TabsContent value="chat" className="space-y-4">
              <ChatTab />
            </TabsContent>

            <TabsContent value="content" className="space-y-4">
              <ContentTab />
            </TabsContent>

            <TabsContent value="podcasts" className="space-y-4">
              <PodcastsTab />
            </TabsContent>

            <TabsContent value="search" className="space-y-4">
              <SearchTab />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  )
}

