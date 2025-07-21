import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useNotebook } from '@/hooks/useNotebook'
import { MessageSquare, Plus, Send, Bot, User } from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function ChatTab() {
  const { conversations, createConversation, sendMessage } = useNotebook()
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)

  const handleCreateConversation = async () => {
    const result = await createConversation('New Conversation')
    if (result.success) {
      setSelectedConversation(result.conversation)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!message.trim() || !selectedConversation || sending) return

    setSending(true)
    const result = await sendMessage(selectedConversation.id, message.trim())
    if (result.success) {
      setMessage('')
      setSelectedConversation(result.data.conversation)
    }
    setSending(false)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
      {/* Conversations List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Conversations</h2>
          <Button size="sm" onClick={handleCreateConversation}>
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>

        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {conversations.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <MessageSquare className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  No conversations yet. Start chatting with your documents!
                </p>
              </CardContent>
            </Card>
          ) : (
            conversations.map((conv) => (
              <Card 
                key={conv.id}
                className={`cursor-pointer transition-colors ${
                  selectedConversation?.id === conv.id 
                    ? 'ring-2 ring-blue-500' 
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
                onClick={() => setSelectedConversation(conv)}
              >
                <CardContent className="p-4">
                  <h3 className="font-medium text-sm mb-1 truncate">
                    {conv.title}
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {conv.message_count || 0} messages
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Chat Interface */}
      <div className="lg:col-span-2">
        {!selectedConversation ? (
          <Card className="h-full">
            <CardContent className="p-8 flex items-center justify-center h-full">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Select a conversation
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Choose a conversation from the list or start a new one to begin chatting.
                </p>
                <Button onClick={handleCreateConversation}>
                  <Plus className="h-4 w-4 mr-2" />
                  Start New Conversation
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex flex-col">
            <CardHeader className="border-b">
              <CardTitle className="text-lg">{selectedConversation.title}</CardTitle>
            </CardHeader>
            
            {/* Messages */}
            <CardContent className="flex-1 p-4 overflow-y-auto">
              <div className="space-y-4">
                {selectedConversation.messages?.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex gap-3 ${
                      msg.type === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {msg.type === 'assistant' && (
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-full">
                        <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                    )}
                    
                    <div className={`max-w-[80%] p-3 rounded-lg ${
                      msg.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    
                    {msg.type === 'user' && (
                      <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-full">
                        <User className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                      </div>
                    )}
                  </div>
                ))}
                
                {sending && (
                  <div className="flex gap-3 justify-start">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-full">
                      <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg">
                      <LoadingSpinner size="sm" />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            
            {/* Message Input */}
            <div className="border-t p-4">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  placeholder="Ask a question about your documents..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  disabled={sending}
                />
                <Button type="submit" disabled={!message.trim() || sending}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

