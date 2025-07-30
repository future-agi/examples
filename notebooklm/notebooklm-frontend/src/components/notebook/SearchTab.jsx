import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useNotebook } from '@/hooks/useNotebook'
import { Search, FileText, ExternalLink, Clock } from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function SearchTab() {
  const { searchNotebook } = useNotebook()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setSearching(true)
    setHasSearched(true)
    
    try {
      const result = await searchNotebook(query.trim())
      if (result.success) {
        setResults(result.results || [])
      } else {
        setResults([])
      }
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setSearching(false)
    }
  }

  const highlightText = (text, query) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className="space-y-6">
      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Your Notebook
          </CardTitle>
          <CardDescription>
            Search across all your documents using semantic search powered by AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search for concepts, topics, or specific information..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" disabled={searching || !query.trim()}>
              {searching ? <LoadingSpinner size="sm" /> : <Search className="h-4 w-4" />}
            </Button>
          </form>
          
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            <p className="mb-2">Search tips:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Use natural language queries like "What are the main benefits?"</li>
              <li>Search for concepts, not just exact words</li>
              <li>Try different phrasings if you don't find what you're looking for</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      {hasSearched && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Search Results
              {!searching && results.length > 0 && (
                <span className="text-sm font-normal text-gray-600 dark:text-gray-400 ml-2">
                  ({results.length} results)
                </span>
              )}
            </h2>
          </div>

          {searching ? (
            <Card>
              <CardContent className="p-8 text-center">
                <LoadingSpinner size="lg" />
                <p className="text-gray-600 dark:text-gray-400 mt-4">
                  Searching through your documents...
                </p>
              </CardContent>
            </Card>
          ) : results.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No results found
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Try different keywords or check your spelling. Make sure you have processed documents in your notebook.
                </p>
                <div className="text-sm text-gray-500 dark:text-gray-500">
                  Searched for: <span className="font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">"{query}"</span>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {results.map((result, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-gray-900 dark:text-white truncate">
                            {result.source_title || 'Untitled Document'}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            {Math.round((result.similarity || 0) * 100)}% match
                          </Badge>
                        </div>
                        
                        <div className="prose dark:prose-invert max-w-none mb-3">
                          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                            {highlightText(result.content || result.text || '', query)}
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                          {result.source_type && (
                            <span>Type: {result.source_type}</span>
                          )}
                          {result.page_number && (
                            <span>Page: {result.page_number}</span>
                          )}
                          {result.created_at && (
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>{formatDate(result.created_at)}</span>
                            </div>
                          )}
                        </div>
                        
                        {result.metadata && (
                          <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                            <details className="cursor-pointer">
                              <summary className="hover:text-gray-700 dark:hover:text-gray-300">
                                View metadata
                              </summary>
                              <pre className="mt-1 p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                                {JSON.stringify(result.metadata, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Search History or Suggestions */}
      {!hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Search Suggestions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-sm text-gray-900 dark:text-white mb-2">
                  Example Queries
                </h4>
                <div className="space-y-2">
                  {[
                    'What are the main conclusions?',
                    'Summarize the key findings',
                    'What methodology was used?',
                    'List the recommendations'
                  ].map((example, index) => (
                    <button
                      key={index}
                      onClick={() => setQuery(example)}
                      className="block w-full text-left text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:underline"
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-sm text-gray-900 dark:text-white mb-2">
                  Search Features
                </h4>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• Semantic search across all documents</li>
                  <li>• Context-aware results</li>
                  <li>• Relevance scoring</li>
                  <li>• Source attribution</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

